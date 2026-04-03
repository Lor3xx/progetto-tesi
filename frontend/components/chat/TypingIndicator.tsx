"use client";

const TypingIndicator = () => {  
	return (
		<div className="message-row assistant">
			<div className="avatar">AI</div>
			<div className="bubble-wrap">
				<div className="bubble bubble-assistant typing">
					<span />
					<span />
					<span />
				</div>
			</div>
		</div>
	);
}

export default TypingIndicator;