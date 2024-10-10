from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, Application, CommandHandler, CallbackContext, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from datetime import datetime 
import logging
import re
import schedule
import time
import threading 
import os
from dotenv import load_dotenv
import traceback
import asyncio 

load_dotenv()  # Load environment variables from .env file

TOKEN = os.getenv('TOKEN')
BOT_USERNAME = os.getenv('BOT_USERNAME')
port = 10000;

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

threading.Thread(target=run_scheduler, daemon=True).start()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Create to-do list and/or reminders for yourself today! \n Type /help for more information!")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Enter every to-do item/alert you would like to add on a new line and send!\n\n FORMAT FOR TASK \n **Task - Details** \n Study Cells (Science) - Page 105 of textbook \n\n FORMAT FOR ALERT \n Yoga at 19:00 today - at Yoga Studio ")
   
async def custom_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Custom Command")

#Responses
def check_match(text):
    match = re.search(r'(.+) at (\d{1,2}:\d{2})(?::\d{2})?', text)  # Modified regex to only capture HH:MM 
    return match 

async def handle_response(update: Update, text: str, context: ContextTypes.DEFAULT_TYPE) -> str:

    #how to handle the text str arg when received
    if text:   

        #CREATING A GREETING HEADER FOR MESSAGE
        greeting = "<code> To-Do List for: </code> "
        emoji_date = "📅" 

        # Create date header and format as DD-MM-YYYY
        formatted_date = f"<b>{datetime.now().strftime('%d-%m-%Y')}</b>"

        if text.splitlines(): 
            keyboard = []

            for index, line in enumerate(text.splitlines()):
                if " at " in line:
                    button_text = line.split('-')[0]
                    # Pass both the index and description as callback data
                    callback_data = f"{index}:{button_text}"  # Example format: index:description
                    keyboard.append([InlineKeyboardButton(
                        text=f"{button_text}", 
                        callback_data=callback_data)])
                
                else: 
                    items = line.split('-')
                    button_text = f"☐ {items[0]}"  # Initial state with checkbox
                    
                    # Pass both the index and description as callback data
                    callback_data = f"{index}:{button_text}"  # Example format: index:description
                    keyboard.append([InlineKeyboardButton(
                        text=f"{button_text}", 
                        callback_data=callback_data)])

            reply_markup = InlineKeyboardMarkup(keyboard)

            # Join formatted_message list into a single string
            full_message =  f"{emoji_date} {greeting} {formatted_date}\n\n"
            
            #Create multi-line todo list 
            return await update.message.reply_text(
                text=full_message,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        
        full_message = f"{emoji_date} {greeting} {formatted_date}\n\n" + "\n".join(text)
        
        #Create single line for to-do list
        return await update.message.reply_text(
                text=full_message,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )

    return await update.message.reply_text(    #Throw Error Message if no text input
            text= 'There was no input! Ask for help using the "/help" command.',
            reply_markup=reply_markup,
            parse_mode='HTML'
    ) 

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    # Search text string for timestamp details
    if update.edited_message :
        context.chat_data['chat_id'] = update.edited_message.chat_id  # Store chat_id in context for retrieval in send_notification
        text = update.edited_message.text
        new_text: str = text.replace(BOT_USERNAME, '').strip()

        # timestamp exists and a scheduled notification is required
        if check_match(new_text):
            await asyncio.gather(handle_response(update, new_text, context), schedule_notification(context, text))
        
        response, reply_markup = await handle_response(update, new_text, context)

    else:  
        context.chat_data['chat_id'] = update.message.chat_id  # Store chat_id in context for retrieval in send_notification
        message_type: str = update.message.chat.type
        text: str = update.message.text
        
        # Differentiate group chat response and private chat response
        if message_type == "supergroup":
            if BOT_USERNAME in text:
                
                new_text: str = text.replace(BOT_USERNAME, '').strip()
                
                #text contains scheduled tasks
                if check_match(new_text): 
                    await asyncio.gather(handle_response(update, new_text, context), schedule_notification(context, text))
                
                else: #text does not contain scheduled tasks 
                    await asyncio.create_task(handle_response(update, text, context))
            
            #group text does not tag bot username - no outcome, ignore the message

        #check non group texts
        elif check_match(text): #if text contains scheduled task 
            await asyncio.gather(handle_response(update, text, context), schedule_notification(context, text))
    
        #text does not contain scheduled tasks
        else: 
            await asyncio.create_task(handle_response(update, text, context))

# Function to schedule a notification based on received message
async def schedule_notification(context: ContextTypes.DEFAULT_TYPE, text: str):

    if text:
        new_text = text.splitlines()
        chat_id = context.chat_data['chat_id'] #This is the chat_id

        for line in new_text:
            new_line = line.split('-')
            match = re.search(r'(.+) at (\d{1,2}:\d{2})(?::\d{2})?', new_line[0])  # Modified regex to only capture HH:MM
        
            if match:
                if BOT_USERNAME in text:
                    task = f"Reminder: {new_line[0].replace(BOT_USERNAME, '').strip()}"
                
                else: 
                    task = f" Reminder: {match.group(1).strip()}" # Extract task

                time_str = match.group(2).strip()  # Extract time (HH:MM)

                # Convert time_str to a datetime object for scheduling
                scheduled_time = datetime.strptime(time_str, "%H:%M").time()
                now = datetime.now()

                # Calculate the time to wait until the scheduled time
                scheduled_datetime = datetime.combine(now.date(), scheduled_time)

                if scheduled_datetime != now:
                    # Calculate how long to wait
                    wait_time = (scheduled_datetime - now).total_seconds()
                    await asyncio.sleep(wait_time)  # Wait until the scheduled time
                    await context.bot.send_message(chat_id, text=task)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Split callback data to get index and description
    try:
        index_str, original_text = query.data.split(':') 
        index = int(index_str)  # Convert index part to integer
    except ValueError:
        await query.answer("Error: Invalid data format.")
        return

    text_lines = query.message.reply_markup.inline_keyboard

    # Get the current text for the selected line
    current_text = text_lines[index][0].text

    # Get the header from the original message
    header = query.message.text.split('\n\n')[0]

    # Determine the new state
    if current_text.startswith("☑️"):
        new_text = original_text[2:]  # Uncheck
        display_text = f"☐ {new_text}"
        # display_text = f"{current_text[2:]}"  # Strikethrough text
    elif current_text.startswith("☐"):
        new_text = original_text[2:] #Check
        display_text = f"~ ☑️ {new_text} ~"
        # display_text = current_text[2:]  # Normal text'

    # Create a new keyboard with updated button text
    new_keyboard = []
    for idx, btn in enumerate(text_lines):
        if idx == index:
                # Update this button with strikethrough if checked
                if current_text.startswith("☑️"):
                    new_keyboard.append([InlineKeyboardButton(display_text, callback_data=f"{idx}:{original_text}")])  # Uncheck
                else:
                    new_keyboard.append([InlineKeyboardButton(display_text, callback_data=f"{idx}:{original_text}")])  # Check
        else:
            new_keyboard.append([InlineKeyboardButton(btn[0].text, callback_data=btn[0].callback_data)])  # Keep other buttons the same
            # new_keyboard.append([InlineKeyboardButton(btn[0].text, callback_data=str(idx))])  # Keep other buttons the same

    new_reply_markup = InlineKeyboardMarkup(new_keyboard)

    # # Edit the message with the updated text and buttons
    # await query.edit_message_reply_markup(reply_markup=new_reply_markup)
    
    # Edit the message text to show the strikethrough
    await context.bot.edit_message_text(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        text= header,
        reply_markup=new_reply_markup,
        parse_mode='HTML'  # Use HTML parsing for strikethrough
    )
    
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Get the traceback details
    tb = traceback.format_exc()

    # Extract the last frame from the traceback
    last_frame = traceback.extract_tb(context.error.__traceback__)[-1]
    line_number = last_frame.lineno  # Get the line number
    filename = last_frame.filename    # Get the filename
    code_line = last_frame.line        # Get the line of code

    # Print the detailed error message
    print(f'Update {update} caused error {context.error}')
    print(f'Error occurred in {filename} at line {line_number}: {code_line}')
    print(f'Traceback details:\n{tb}')

def main():
    app = Application.builder().token(TOKEN).build()

    #Commands
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('custom', custom_command))
    app.add_handler(CommandHandler("schedule", schedule_notification))

    #Messages 
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    #Handling states
    app.add_handler(CallbackQueryHandler(button_callback))
    
    #Errors
    app.add_error_handler(error)

    #Polls the bot 
    app.run_polling(poll_interval=2)

if __name__ == '__main__': 
    print('Starting bot...')
    asyncio.run(main())
