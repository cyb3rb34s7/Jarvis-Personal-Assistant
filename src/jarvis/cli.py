"""JARVIS - CLI interface."""

import asyncio
import sys
import warnings

# Suppress Pydantic v1 warning
warnings.filterwarnings("ignore", message="Core Pydantic V1 functionality")

import click

from .agent import create_agent, run_agent, create_agent_async, run_agent_async
from .config import get_config
from .memory import SessionMemory, get_or_create_session
from .utils import format_error_for_user, check_ollama_running


# Known subcommands for detection
SUBCOMMANDS = {"calc", "mcp-status", "ask", "config", "status", "chat", "history"}


@click.group(invoke_without_command=True)
@click.option("--model", default=None, help="Ollama model to use")
@click.option("--voice", "-v", is_flag=True, help="Enable voice input mode")
@click.option("--mcp", is_flag=True, help="Enable MCP tools")
@click.option("--session", "-s", default=None, help="Resume conversation by ID")
@click.option("--verbose", is_flag=True, help="Enable verbose output")
@click.pass_context
def cli(ctx, model, voice, mcp, session, verbose):
    """JARVIS - Local voice AI assistant.

    Ask a question: jarvis "what is 2+2"

    With memory: jarvis chat (starts interactive session)

    With MCP tools: jarvis --mcp "search for langchain"

    Voice mode: jarvis --voice

    Show status: jarvis status
    """
    # Load configuration
    config = get_config()

    # Override with CLI options
    model = model or config.model.name
    mcp = mcp or config.mcp.enabled
    verbose = verbose or config.verbose

    ctx.ensure_object(dict)
    ctx.obj["model"] = model
    ctx.obj["mcp"] = mcp
    ctx.obj["session_id"] = session
    ctx.obj["verbose"] = verbose
    ctx.obj["config"] = config

    if voice:
        _run_voice_mode(model, use_mcp=mcp, verbose=verbose)
    elif ctx.invoked_subcommand is None:
        remaining = ctx.args
        if remaining:
            query = " ".join(remaining)
            _run_query(query, model, mcp, verbose)


@cli.command()
@click.argument("query")
@click.pass_context
def ask(ctx, query):
    """Ask JARVIS a question.

    Example: jarvis ask "what is 2+2"
    """
    model = ctx.obj.get("model")
    mcp = ctx.obj.get("mcp", False)
    verbose = ctx.obj.get("verbose", False)
    _run_query(query, model, mcp, verbose)


def _run_query(query: str, model: str, mcp: bool, verbose: bool):
    """Run a query and print response."""
    try:
        # Check Ollama is running
        if not check_ollama_running():
            click.echo("Error: Ollama is not running. Start it with: ollama serve")
            return

        if mcp:
            response = asyncio.run(_run_query_async(query, model))
        else:
            agent = create_agent(model=model)
            response = run_agent(query, agent)

        click.echo(response)

    except KeyboardInterrupt:
        click.echo("\nCancelled.")
    except Exception as e:
        error_msg = format_error_for_user(e)
        click.echo(f"Error: {error_msg}")
        if verbose:
            import traceback
            traceback.print_exc()


async def _run_query_async(query: str, model: str) -> str:
    """Run a query with MCP tools enabled."""
    agent = await create_agent_async(model=model)
    return await run_agent_async(query, agent)


def _run_voice_mode(model: str, use_mcp: bool = False, verbose: bool = False):
    """Run in voice input/output mode with session memory."""
    try:
        from .voice import PushToTalk, get_tts
    except ImportError as e:
        click.echo(f"Error: Voice dependencies not installed. Run: pip install jarvis[voice]")
        click.echo(f"Details: {e}")
        return

    # Check Ollama is running
    if not check_ollama_running():
        click.echo("Error: Ollama is not running. Start it with: ollama serve")
        return

    try:
        # Create agent (with or without MCP)
        if use_mcp:
            click.echo("[Voice] Loading agent with MCP tools...")
            agent = asyncio.run(create_agent_async(model=model))
        else:
            agent = create_agent(model=model)

        tts = get_tts()

        # Create session for voice mode (entire session shares context)
        session = SessionMemory()
        click.echo(f"[Voice] Session: {session.conversation_id}")

    except Exception as e:
        error_msg = format_error_for_user(e)
        click.echo(f"Error initializing: {error_msg}")
        if verbose:
            import traceback
            traceback.print_exc()
        return

    def handle_speech(text: str):
        """Process speech input with session context."""
        if text.lower() in ("exit", "quit", "stop", "goodbye", "bye"):
            click.echo("Goodbye!")
            try:
                tts.speak("Goodbye!")
            except Exception:
                pass
            raise SystemExit(0)

        try:
            # Run with session memory - JARVIS remembers the conversation
            response = run_agent(text, agent, session=session)
            click.echo(f"\nJARVIS: {response}\n")
            tts.speak(response)
        except Exception as e:
            error_msg = format_error_for_user(e)
            click.echo(f"Error: {error_msg}")
            try:
                tts.speak("Sorry, I encountered an error.")
            except Exception:
                pass

    click.echo("\n" + "=" * 50)
    click.echo("  JARVIS Voice Mode" + (" [MCP]" if use_mcp else "") + " [Memory]")
    click.echo("=" * 50)
    click.echo("\n  Press Ctrl+Space and speak")
    click.echo("  Say 'exit' to stop | Ctrl+C to force quit")
    click.echo("=" * 50 + "\n")

    ptt = PushToTalk(on_speech=handle_speech)

    try:
        ptt.start()
        import time
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        click.echo("\nGoodbye!")
    except Exception as e:
        click.echo(f"Error: {format_error_for_user(e)}")
    finally:
        ptt.stop()


@cli.command()
@click.argument("expression")
def calc(expression):
    """Calculate a math expression directly."""
    from .agent.tools import calculator
    result = calculator.invoke(expression)
    click.echo(result)


@cli.command("mcp-status")
def mcp_status():
    """Show status of configured MCP servers."""
    from .agent.mcp_loader import get_mcp_config_path
    import json

    config_path = get_mcp_config_path()

    if not config_path.exists():
        click.echo(f"No MCP config found at: {config_path}")
        click.echo("\nCreate data/mcp_servers.json to configure MCP servers.")
        return

    try:
        with open(config_path) as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        click.echo(f"Error: Invalid JSON in {config_path}")
        click.echo(f"Details: {e}")
        return

    servers = config.get("mcpServers", {})

    if not servers:
        click.echo("No MCP servers configured.")
        return

    click.echo(f"\nMCP Servers ({len(servers)} configured):")
    click.echo("-" * 40)

    for name, server_config in servers.items():
        transport = server_config.get("transport", "unknown")
        if transport == "http":
            url = server_config.get("url", "N/A")
            click.echo(f"  {name}: HTTP -> {url}")
        elif transport == "stdio":
            cmd = server_config.get("command", "N/A")
            args = " ".join(server_config.get("args", []))
            click.echo(f"  {name}: stdio -> {cmd} {args}")
        else:
            click.echo(f"  {name}: {transport}")

    click.echo("-" * 40)
    click.echo(f"\nConfig: {config_path}")
    click.echo("Usage: jarvis --mcp ask \"your query\"")


@cli.command()
def status():
    """Show JARVIS status and configuration."""
    from .utils import check_dependencies
    from .config import get_config, CONFIG_PATH
    from .database import list_conversations, get_db_path

    config = get_config()
    deps = check_dependencies()

    click.echo("\n" + "=" * 40)
    click.echo("  JARVIS Status")
    click.echo("=" * 40)

    # Dependencies
    click.echo("\nDependencies:")
    click.echo(f"  Ollama:         {'OK' if deps['ollama'] else 'NOT RUNNING'}")
    click.echo(f"  faster-whisper: {'OK' if deps['faster_whisper'] else 'Not installed'}")
    click.echo(f"  kokoro-onnx:    {'OK' if deps['kokoro_onnx'] else 'Not installed'}")
    click.echo(f"  sounddevice:    {'OK' if deps['sounddevice'] else 'Not installed'}")

    # Configuration
    click.echo("\nConfiguration:")
    click.echo(f"  Model:      {config.model.name}")
    click.echo(f"  STT Model:  {config.voice.stt_model}")
    click.echo(f"  Hotkey:     {config.voice.hotkey}")
    click.echo(f"  MCP:        {'Enabled' if config.mcp.enabled else 'Disabled'}")

    # Memory
    click.echo("\nMemory:")
    conversations = list_conversations(limit=1000)
    click.echo(f"  Conversations: {len(conversations)}")
    click.echo(f"  Database: {get_db_path()}")

    # Paths
    click.echo("\nPaths:")
    click.echo(f"  Config: {CONFIG_PATH}")
    click.echo(f"  Notes:  {config.notes_dir}")

    click.echo("\n" + "=" * 40)


@cli.command()
def config():
    """Show configuration file location."""
    from .config import CONFIG_PATH

    click.echo(f"Config file: {CONFIG_PATH}")
    click.echo("\nEdit this file to customize JARVIS settings.")

    if CONFIG_PATH.exists():
        click.echo("\nCurrent settings:")
        with open(CONFIG_PATH) as f:
            click.echo(f.read())


@cli.command()
@click.option("--resume", "-r", is_flag=True, help="Resume last conversation")
@click.option("--id", "conv_id", default=None, help="Resume specific conversation ID")
@click.pass_context
def chat(ctx, resume, conv_id):
    """Start an interactive chat session with memory.

    JARVIS will remember the conversation context.

    Example:
        jarvis chat              # New conversation
        jarvis chat --resume     # Resume last conversation
        jarvis chat --id abc123  # Resume specific conversation
    """
    model = ctx.obj.get("model")
    mcp = ctx.obj.get("mcp", False)
    verbose = ctx.obj.get("verbose", False)

    # Check Ollama is running
    if not check_ollama_running():
        click.echo("Error: Ollama is not running. Start it with: ollama serve")
        return

    try:
        # Create agent
        if mcp:
            click.echo("[Chat] Loading agent with MCP tools...")
            agent = asyncio.run(create_agent_async(model=model))
        else:
            agent = create_agent(model=model)

        # Create or resume session
        if conv_id:
            session = SessionMemory(conversation_id=conv_id)
            click.echo(f"[Chat] Resuming conversation: {conv_id}")
        elif resume:
            session = get_or_create_session(resume_latest=True)
            click.echo(f"[Chat] Resuming conversation: {session.conversation_id}")
        else:
            session = SessionMemory()
            click.echo(f"[Chat] New conversation: {session.conversation_id}")

    except Exception as e:
        error_msg = format_error_for_user(e)
        click.echo(f"Error initializing: {error_msg}")
        if verbose:
            import traceback
            traceback.print_exc()
        return

    click.echo("\n" + "=" * 50)
    click.echo("  JARVIS Chat Mode" + (" [MCP]" if mcp else "") + " [Memory]")
    click.echo("=" * 50)
    click.echo("  Type your message and press Enter")
    click.echo("  Type 'exit' to quit | Ctrl+C to force quit")
    click.echo("=" * 50 + "\n")

    try:
        while True:
            try:
                user_input = input("You: ").strip()
            except EOFError:
                break

            if not user_input:
                continue

            if user_input.lower() in ("exit", "quit", "bye"):
                click.echo("Goodbye!")
                break

            try:
                response = run_agent(user_input, agent, session=session)
                click.echo(f"\nJARVIS: {response}\n")
            except Exception as e:
                error_msg = format_error_for_user(e)
                click.echo(f"Error: {error_msg}")

    except KeyboardInterrupt:
        click.echo("\nGoodbye!")


@cli.command()
@click.option("--limit", "-n", default=10, help="Number of conversations to show")
def history(limit):
    """Show recent conversation history.

    Example:
        jarvis history           # Show last 10 conversations
        jarvis history -n 20     # Show last 20 conversations
    """
    from .database import list_conversations, get_messages

    conversations = list_conversations(limit=limit)

    if not conversations:
        click.echo("No conversations found.")
        return

    click.echo("\n" + "=" * 60)
    click.echo("  Recent Conversations")
    click.echo("=" * 60)

    for conv in conversations:
        # Get message count
        messages = get_messages(conv.id, limit=1000)
        msg_count = len(messages)

        title = conv.title or "(untitled)"
        if len(title) > 40:
            title = title[:40] + "..."

        click.echo(f"\n  ID: {conv.id}")
        click.echo(f"  Title: {title}")
        click.echo(f"  Messages: {msg_count}")
        click.echo(f"  Updated: {conv.updated_at}")
        click.echo("-" * 60)

    click.echo("\nResume a conversation:")
    click.echo("  jarvis chat --id <conversation_id>")
    click.echo("  jarvis chat --resume  (resumes most recent)")


def main():
    """Entry point."""
    args = sys.argv[1:]

    # Convert direct query to 'ask' command
    if args and not args[0].startswith("-") and args[0] not in SUBCOMMANDS:
        sys.argv = [sys.argv[0], "ask"] + args

    try:
        cli(obj={})
    except Exception as e:
        click.echo(f"Error: {format_error_for_user(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
