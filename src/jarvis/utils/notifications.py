"""JARVIS - Windows notifications."""

import subprocess
import sys


def show_notification(title: str, message: str) -> bool:
    """Show a Windows toast notification.

    Args:
        title: Notification title
        message: Notification body

    Returns:
        True if notification was shown successfully
    """
    try:
        # Use PowerShell for Windows toast notifications
        ps_script = f'''
        [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
        [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null

        $template = @"
        <toast>
            <visual>
                <binding template="ToastText02">
                    <text id="1">{title}</text>
                    <text id="2">{message}</text>
                </binding>
            </visual>
            <audio src="ms-winsoundevent:Notification.Default"/>
        </toast>
"@

        $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
        $xml.LoadXml($template)
        $toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
        [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("JARVIS").Show($toast)
        '''

        subprocess.run(
            ["powershell", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
            capture_output=True,
            timeout=5
        )
        return True
    except Exception as e:
        # Fallback: print to console
        print(f"\n🔔 {title}: {message}")
        return False


if __name__ == "__main__":
    # Test notification
    show_notification("JARVIS", "Test notification!")
