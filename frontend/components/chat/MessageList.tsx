"use client"
import { useState } from "react";
import { Message } from "@/types";
import MessageBubble from "./MessageBubble"

const MessageList = () => {
    const [messages, setMessages] = useState<Message[]>([]);
    const visibleMessages = messages;
    return (
        <div>
            {visibleMessages.map((msg) => (
				<MessageBubble key={msg.id} msg={msg} />
			))}
        </div>
    )
}

export default MessageList