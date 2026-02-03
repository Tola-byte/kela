import "./globals.css";

export const metadata = {
  title: "Memory Infrastructure Dashboard",
  description: "Debug console for memory infrastructure",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
