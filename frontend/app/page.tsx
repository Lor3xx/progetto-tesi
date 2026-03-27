import ChatBody from "@/components/chat/ChatBody";
import InputBar from "@/components/layout/InputBar";
import Navbar from "@/components/layout/Navbar";
 
export default function Home() {
	return (
		<div>
			<div className="page">
				{/* ── Header ── */}
				<Navbar/>

				{/* ── Chat area ── */}
				<ChatBody />

			</div>
		</div>
	);
}
