import ChatBody from "@/components/chat/ChatBody";
import Navbar from "@/components/layout/Navbar";
import Sidebar from "@/components/layout/Sidebar";
 
export default function Home() {
	return (
		<div className="app-root">
			<Sidebar />
			<div className="page">
				{/* ── Header ── */}
				<Navbar/>

				{/* ── Chat area ── */}
				<ChatBody />

			</div>
		</div>
	);
}
