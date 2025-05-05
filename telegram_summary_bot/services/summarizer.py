"""
Message summarization service.
"""

import logging

# Get the logger from the config module
logger = logging.getLogger("telegram_summary_bot.config")

from telegram_summary_bot.utils.storage import group_members, thread_titles
from telegram_summary_bot.services.ai_generator import generate_with_ollama


def summarize_messages(threaded_messages):
    """
    Summarize messages from different threads.
    
    Args:
        threaded_messages (dict): A dictionary of thread IDs to message lists
        
    Returns:
        str: The generated summary
    """
    if not threaded_messages:
        return "No messages in the selected timeframe."

    member_list = ", ".join(group_members.values())
    prompt_sections = []

    for thread_id, messages in threaded_messages.items():
        # Group messages by user for this thread
        user_messages = {}
        # Initialize with all group members to ensure everyone is included
        for user_id, display_name in group_members.items():
            user_messages[user_id] = []
        
        # Now add the actual messages
        for msg in messages:
            user_id = str(msg["user_id"])  # Ensure user_id is a string to match group_members keys
            if user_id in user_messages:
                user_messages[user_id].append(msg)
            else:
                # Handle messages from users not in group_members
                user_messages[user_id] = [msg]
        
        # Format messages by user
        user_conversations = []
        for user_id, msgs in user_messages.items():
            display_name = group_members.get(user_id, "Unknown User")
            if msgs:
                messages_text = "\n".join([
                    f"[{m['time'].strftime('%H:%M')}]: {m['text']}"
                    for m in msgs
                ])
                user_conversations.append(f"{display_name}:\n{messages_text}")
            else:
                user_conversations.append(f"{display_name}: No messages in this timeframe.")
        
        conversation = "\n\n".join(user_conversations)
        thread_title = thread_titles.get(thread_id, f"Thread {thread_id}")
        if thread_id == 0 and thread_title == "Thread 0":
            thread_title = "Main Group Chat"

        prompt_sections.append(
            f"[Topic: {thread_title}]\n"
            f"Messages:\n{conversation}"
        )

    # If there's only one section and it's the main group chat, simplify the prompt
    if len(prompt_sections) == 1 and "Main Group Chat" in prompt_sections[0]:
        full_prompt = (
            "These are chat messages from a Telegram group.\n\n"
            "For each member of the group:\n\n"
            "- If they spoke in the chat, summarize their messages.\n"
            "- If they didn't speak, write: 'Did not participate.'\n\n"
            f"Group members: {member_list}\n\n"
            + prompt_sections[0]
        )
    else:
        full_prompt = (
            "These are categorized chat messages from a Telegram group.\n\n"
            "For each topic, list all group members by name. For each member:\n\n"
            "- If they spoke in that topic, summarize their message.\n"
            "- If they didn't speak, write: 'Did not participate.'\n\n"
            f"Group members: {member_list}\n\n"
            + "\n".join(prompt_sections)
        )
    
    # Use Ollama directly
    logger.info("Generating summary using Ollama")
    return generate_with_ollama(full_prompt) 