using System;
using System.Diagnostics;
using System.IO;
using System.Net.Sockets;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using System.Windows.Media.Imaging;

namespace TrayApp
{
    public partial class TrayPopup : Window
    {
        private readonly string baseDir = @"D:\Scripts\Mathias\RemoteShutdown\Webserver+Tray V2";

        private readonly (string name, int port)[] services =
        {
            ("sonarr", 8989),
            ("radarr", 7878),
            ("bazarr", 6767),
            ("tdarr", 8265),
            ("sabnzbd", 6969),
            ("jellyfin", 8096),
            ("plex", 32400),
            ("jellyseerr", 5055)
        };

        private readonly double scale = 1.5;

        public TrayPopup()
        {
            InitializeComponent();
            BuildServiceList();
        }

        private void BuildServiceList()
        {
            ServiceList.Children.Clear();

            foreach (var (name, port) in services)
            {
                bool running = IsPortOpen("127.0.0.1", port);
                var bgColor = running ? Brushes.Green : Brushes.Red;
                string statusEmoji = running ? "🟢" : "🔴";

                var row = new Border
                {
                    Background = bgColor,
                    CornerRadius = new CornerRadius(8),
                    Margin = new Thickness(0, 5, 0, 5),
                    Padding = new Thickness(5)
                };

                var stack = new StackPanel
                {
                    Orientation = Orientation.Horizontal
                };

                // Load icon
                string iconPath = Path.Combine(baseDir, "static", "img", "32px", $"{name}_32px.png");
                var icon = new Image
                {
                    Width = 32 * scale,
                    Height = 32 * scale,
                    Margin = new Thickness(5)
                };
                if (File.Exists(iconPath))
                    icon.Source = new BitmapImage(new Uri(iconPath));

                var label = new TextBlock
                {
                    Text = $"{statusEmoji} {char.ToUpper(name[0]) + name.Substring(1)}",
                    FontSize = 12 * scale,
                    VerticalAlignment = VerticalAlignment.Center,
                    Foreground = Brushes.White,
                    Margin = new Thickness(10, 0, 0, 0)
                };

                stack.Children.Add(icon);
                stack.Children.Add(label);

                row.Child = stack;

                row.MouseLeftButtonUp += (s, e) =>
                {
                    Process.Start(new ProcessStartInfo
                    {
                        FileName = $"http://localhost:{port}",
                        UseShellExecute = true
                    });
                    this.Hide();
                };

                ServiceList.Children.Add(row);
            }

            // Exit button
            var exitBtn = new Button
            {
                Content = "Exit",
                FontSize = 12 * scale,
                Margin = new Thickness(0, 10, 0, 0),
                Background = Brushes.Gray,
                Foreground = Brushes.White,
                Padding = new Thickness(5),
                HorizontalAlignment = HorizontalAlignment.Stretch,
                BorderThickness = new Thickness(0),
                Cursor = System.Windows.Input.Cursors.Hand
            };
            exitBtn.Click += (s, e) => Application.Current.Shutdown();
            ServiceList.Children.Add(exitBtn);
        }

        private bool IsPortOpen(string host, int port)
        {
            try
            {
                using (var client = new TcpClient())
                {
                    var result = client.BeginConnect(host, port, null, null);
                    bool success = result.AsyncWaitHandle.WaitOne(TimeSpan.FromMilliseconds(200));
                    return success && client.Connected;
                }
            }
            catch
            {
                return false;
            }
        }
    }
}
