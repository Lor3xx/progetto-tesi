"use client";

import { useState } from "react";
import MessageList from "./MessageList";
import TypingIndicator from "./TypingIndicator";

const ChatBody = () => {
    const [loading, setLoading] = useState(false);
    
    return (
        <div className="chat-area">
			<MessageList />
			{loading && <TypingIndicator />}
		</div>
    )
}

export default ChatBody