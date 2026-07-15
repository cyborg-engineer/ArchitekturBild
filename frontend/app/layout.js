import "./globals.css";

export const metadata = {
  title: "ArchitekturBild",
  description: "MVP for image-to-description workflow"
};

export default function RootLayout({ children }) {
  return (
    <html lang="de">
      <body>{children}</body>
    </html>
  );
}
