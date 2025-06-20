import { createContext, useContext, useState } from 'react';
import { ulid } from 'ulid';

// Chat Context for managing messages
const ChatContext = createContext();
export const useChat = () => useContext(ChatContext);

// Simple text decoder helper (browser equivalent of Node's TextDecoder)
const decodeUTF8 = (bytes) => {
  return new TextDecoder('utf-8').decode(bytes);
};

export function ChatProvider({ children }) {
  const [messages, setMessages] = useState([]);
  const [activityId, setActivityId] = useState(null);
  const [loading, setLoading] = useState(false);
  
  // Hardcoded agent info
  const [agent, setSelectedAgent] = useState({
    name: "Gas Genie",
    description: "AI-powered gas price predictor and transaction optimizer",
    _id: "gas-genie"
  });

  // Function to send a message to the agent
  const sendMessage = async (prompt) => {
    setLoading(true);
    try {
      // Generate IDs using proper ULID format
      const newActivityId = activityId || ulid();
      const requestId = ulid();
      
      // Format the request body to match the exact format
      const body = {
        query: {
          id: ulid(),  // Valid ULID format
          prompt: prompt
        },
        session: {
          processor_id: "test-processor",
          activity_id: newActivityId,
          request_id: requestId,
          interactions: []
        }
      };
      
      console.log('Sending message to agent:', body);

      // Use fetch with streaming for SSE responses
      const response = await fetch('/assist', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'text/event-stream'
          },
          body: JSON.stringify(body)
      });
      
          if (!response.ok) {
            throw new Error('Failed to get response from agent');
          }
          
          // Save the activity ID for the next request
          setActivityId(newActivityId);

          // Set up a reader for the stream
          const reader = response.body.getReader();
          let buffer = '';
          let answer = '';
          
      while (true) {
        const { done, value } = await reader.read();
        
              if (done) {
                console.log('Stream ended, resolving with answer:', answer);
          return answer.trim() || 'No response received from agent.';
              }
              
              // Decode the chunk and process it
              const chunk = typeof value === 'string' ? value : decodeUTF8(value);
        console.log('Received raw chunk:', chunk);
              
              buffer += chunk;
              
              // Split on double-newline - standard SSE frame separator
              const frames = buffer.split('\n\n');
              buffer = frames.pop(); // last piece might be incomplete
              
              for (const frame of frames) {
          if (!frame.trim()) continue;
          
          try {
            // Parse the SSE data
            const data = JSON.parse(frame.replace('data: ', ''));
            console.log('Parsed SSE data:', data);
            
            switch (data.type) {
              case 'message':
                answer += data.content;
                console.log('Updated answer:', answer);
                break;
              case 'error':
                console.error('Error from agent:', data.content);
                return `Error: ${data.content}`;
              case 'done':
                console.log('Stream completed');
                return answer.trim() || 'No response received from agent.';
              default:
                console.warn('Unknown event type:', data.type);
                  }
                } catch (err) {
                  console.error('Error processing frame:', err);
            console.error('Problematic frame:', frame);
          }
        }
      }
    } catch (error) {
      console.error('Error communicating with agent:', error);
      return 'Error: Could not connect to your local agent. Make sure it\'s running on localhost:8000';
    } finally {
      setLoading(false);
    }
  };

  return (
    <ChatContext.Provider value={{ 
      messages, 
      setMessages, 
      agent, 
      setSelectedAgent,
      sendMessage,
      loading,
      setLoading,
      activityId
    }}>
      {children}
    </ChatContext.Provider>
  );
} 