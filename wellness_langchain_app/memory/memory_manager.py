"""
Memory management system with short-term, long-term memory and compaction
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()


class MemoryManager:
    """Manages user memories with automatic compaction and summarization"""
    
    def __init__(self, data_dir: str = "data/memories"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Configuration
        self.short_term_limit = 10  # Max short-term memories before compaction
        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0.3,
            groq_api_key=os.getenv("GROQ_API_KEY")
        )
    
    def _get_user_file(self, user_id: str) -> Path:
        """Get the memory file path for a user"""
        return self.data_dir / f"{user_id}_memories.json"
    
    def _load_memories(self, user_id: str) -> Dict:
        """Load all memories for a user"""
        file_path = self._get_user_file(user_id)
        
        if not file_path.exists():
            return {
                "user_id": user_id,
                "short_term": [],
                "long_term": [],
                "compaction_count": 0,
                "created_at": datetime.now().isoformat()
            }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                # Check if file is empty
                if not content:
                    return {
                        "user_id": user_id,
                        "short_term": [],
                        "long_term": [],
                        "compaction_count": 0,
                        "created_at": datetime.now().isoformat()
                    }
                return json.loads(content)
        except (json.JSONDecodeError, ValueError) as e:
            # File is corrupted, return fresh structure
            print(f"Warning: Corrupted memory file for {user_id}: {e}")
            return {
                "user_id": user_id,
                "short_term": [],
                "long_term": [],
                "compaction_count": 0,
                "created_at": datetime.now().isoformat()
            }
    
    def _save_memories(self, user_id: str, memories: Dict):
        """Save memories to file"""
        file_path = self._get_user_file(user_id)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(memories, f, indent=2, ensure_ascii=False)
    
    def add_memory(self, user_id: str, memory_type: str, content: str, metadata: Optional[Dict] = None):
        """
        Add a new memory for the user
        
        Args:
            user_id: User identifier
            memory_type: Type of memory (interaction, action, preference, etc.)
            content: Memory content
            metadata: Additional metadata (agent used, topic, etc.)
        """
        memories = self._load_memories(user_id)
        
        memory_entry = {
            "type": memory_type,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        memories["short_term"].append(memory_entry)
        
        # Check if compaction is needed
        if len(memories["short_term"]) >= self.short_term_limit:
            self._compact_memories(user_id, memories)
        
        self._save_memories(user_id, memories)
    
    def _compact_memories(self, user_id: str, memories: Dict):
        """
        Compact short-term memories into a summary
        Uses LLM to create a coherent summary of recent interactions
        """
        if len(memories["short_term"]) < 3:
            return  # Not enough to compact
        
        # Prepare memories for summarization
        memory_text = "\n\n".join([
            f"[{m['timestamp']}] {m['type']}: {m['content']}"
            for m in memories["short_term"]
        ])
        
        prompt = f"""Summarize the following user interactions and actions into a concise memory summary.
Focus on:
- User preferences and choices
- Goals and objectives mentioned
- Important actions taken
- Patterns in behavior

Memories to summarize:
{memory_text}

Provide a brief, coherent summary (2-3 sentences max):"""
        
        try:
            response = self.llm.invoke(prompt)
            summary = response.content.strip()
            
            # Add to long-term memory
            memories["long_term"].append({
                "summary": summary,
                "period": {
                    "start": memories["short_term"][0]["timestamp"],
                    "end": memories["short_term"][-1]["timestamp"]
                },
                "compacted_at": datetime.now().isoformat(),
                "original_count": len(memories["short_term"])
            })
            
            # Clear short-term, keeping only the most recent 2
            memories["short_term"] = memories["short_term"][-2:]
            memories["compaction_count"] += 1
            
        except Exception as e:
            print(f"Memory compaction error: {e}")
            # On error, just move old memories to long-term without summarization
            memories["long_term"].append({
                "summary": f"Batch of {len(memories['short_term'])} interactions",
                "period": {
                    "start": memories["short_term"][0]["timestamp"],
                    "end": memories["short_term"][-1]["timestamp"]
                }
            })
            memories["short_term"] = memories["short_term"][-2:]
    
    def get_memories(self, user_id: str, limit: Optional[int] = None) -> List[Dict]:
        """Get recent short-term memories"""
        memories = self._load_memories(user_id)
        short_term = memories.get("short_term", [])
        
        if limit:
            return short_term[-limit:]
        return short_term
    
    def get_long_term_memories(self, user_id: str) -> List[Dict]:
        """Get all long-term memory summaries"""
        memories = self._load_memories(user_id)
        return memories.get("long_term", [])
    
    def get_context(self, user_id: str, max_recent: int = 5) -> str:
        """
        Build a context string for the agent from memories
        
        Args:
            user_id: User identifier
            max_recent: Number of recent short-term memories to include
            
        Returns:
            Formatted context string
        """
        memories = self._load_memories(user_id)
        
        context_parts = []
        
        # Add long-term memory summaries
        if memories.get("long_term"):
            context_parts.append("## Previous Interactions Summary:")
            for lt_mem in memories["long_term"][-3:]:  # Last 3 summaries
                context_parts.append(f"- {lt_mem['summary']}")
        
        # Add recent short-term memories
        if memories.get("short_term"):
            context_parts.append("\n## Recent Interactions:")
            for st_mem in memories["short_term"][-max_recent:]:
                context_parts.append(f"- [{st_mem['type']}] {st_mem['content']}")
        
        return "\n".join(context_parts) if context_parts else "No previous interactions."
    
    def clear_memories(self, user_id: str):
        """Clear all memories for a user"""
        file_path = self._get_user_file(user_id)
        if file_path.exists():
            file_path.unlink()


if __name__ == "__main__":
    # Test the memory manager
    mm = MemoryManager()
    
    test_user = "test_user_123"
    
    # Add some test memories
    mm.add_memory(test_user, "action", "User requested a workout plan for fat loss")
    mm.add_memory(test_user, "preference", "User prefers morning workouts")
    mm.add_memory(test_user, "action", "Completed yoga session")
    
    print("Recent memories:")
    for mem in mm.get_memories(test_user):
        print(f"  {mem['type']}: {mem['content']}")
    
    print("\nContext for agent:")
    print(mm.get_context(test_user))
