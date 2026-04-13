"use client"
import { Message } from "@/types";
import MessageBubble from "./MessageBubble"

const MessageList = ({ messages, threadId }: { messages: Message[]; threadId: string | null }) => {
    const visibleMessages = messages;
    return (
        <div>
            {visibleMessages.map((msg) => (
				<MessageBubble key={msg.id} msg={msg} threadId={threadId} />
			))}
        </div>
    )
}

export default MessageList