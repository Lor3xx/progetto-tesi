import ChatBody from "@/components/chat/ChatBody";
import Header from "@/components/layout/Header";
import Sidebar from "@/components/layout/Sidebar";
 
export default function Home() {
	return (
		<div className="app-root">
			<Sidebar />
			<div className="page">
				{/* ── Header ── */}
				<Header />

				{/* ── Chat area ── */}
				<ChatBody />

			</div>
		</div>
	);
}
