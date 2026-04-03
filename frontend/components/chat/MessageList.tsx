"use client"
import { Message } from "@/types";
import MessageBubble from "./MessageBubble"

const MessageList = ({ messages }: { messages: Message[] }) => {
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