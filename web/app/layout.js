import './globals.css';

export const metadata = {
  title: 'Discord Bot Dashboard',
  description: 'Guild modules dashboard'
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
