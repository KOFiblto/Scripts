using System;
using System.Drawing;
using System.Windows;
using WinForms = System.Windows.Forms; // alias
using System.Diagnostics;

namespace TrayApp
{
    public partial class App : Application
    {
        private WinForms.NotifyIcon trayIcon;
        private TrayPopup popup;

        private void Application_Startup(object sender, StartupEventArgs e)
        {
            // Create tray icon
            trayIcon = new WinForms.NotifyIcon
            {
                Text = "Service Tray",
                Icon = new Icon(SystemIcons.Application, 32, 32),
                Visible = true
            };

            trayIcon.MouseUp += TrayIcon_MouseUp;

            // Create popup window
            popup = new TrayPopup();
            popup.Topmost = true;
        }

        private void TrayIcon_MouseUp(object sender, WinForms.MouseEventArgs e)
        {
            if (e.Button == WinForms.MouseButtons.Right)
            {
                var mouse = WinForms.Control.MousePosition;

                popup.WindowStartupLocation = WindowStartupLocation.Manual;

                // Position near tray
                popup.Left = mouse.X - popup.Width;
                popup.Top = mouse.Y - popup.Height;

                if (!popup.IsVisible)
                    popup.Show();
                else
                {
                    popup.Hide();
                    popup.Show();
                }

                popup.Activate();
            }
        }

        private void Application_Exit(object sender, ExitEventArgs e)
        {
            trayIcon.Visible = false;
        }
    }
}
