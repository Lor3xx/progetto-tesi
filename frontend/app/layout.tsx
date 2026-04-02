import type { Metadata } from "next";
import "../styles/globals.css";


export const metadata: Metadata = {
	title: "RAG Document Search",
	description: "A RAG chatbot specialized in document search about cybersecurity topics.",
};

export default function RootLayout({
  	children,
}: Readonly<{
  	children: React.ReactNode;
}>) {
	return (
		<html
		lang="en"
		className="h-full antialiased"
		>
			<body>
				<main>
					{children}
				</main>
			</body>
		</html>
	);
}
