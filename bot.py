from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import requests
import csv
import io
import random
import time
import os
from datetime import datetime

BOT_TOKEN = 'YOUR_BOT_TOKEN'

CSV_URL_AYA = 'https://docs.google.com/spreadsheets/d/1RvSq_A1HPPv4bLvby9Ez4e5vMV9_T7qVNUPHu5AX_ZQ/gviz/tq?tqx=out:csv&sheet=aya'
CSV_URL_COMPLETE = 'https://docs.google.com/spreadsheets/d/1Hlg56BLG0X_QZC_cAyIj5VMsq79Omeg6PlUW1XQfkfI/gviz/tq?tqx=out:csv&sheet=complete'

def load_questions(url):
response = requests.get(url)
data = response.content.decode('utf-8')
reader = csv.DictReader(io.StringIO(data))
return list(reader)

questions_aya = load_questions(CSV_URL_AYA)
questions_complete = load_questions(CSV_URL_COMPLETE)

def start(update: Update, context: CallbackContext):
update.message.reply_text("✍️ من فضلك، أدخل اسمك قبل البدء:")
context.user_data.clear()
context.user_data['awaiting_name'] = True

def save_result(name, score):
filename = 'results.csv'
file_exists = os.path.isfile(filename)
with open(filename, mode='a', newline='', encoding='utf-8') as file:
writer = csv.writer(file)
if not file_exists:
writer.writerow(['الاسم', 'النتيجة', 'التاريخ'])
writer.writerow([name, score, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])

def select_test_type(update: Update, context: CallbackContext):
keyboard = [['آيات', 'إكمال']]
reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
update.message.reply_text("📚 اختر نوع الاختبار:", reply_markup=reply_markup)

def select_surah(update: Update, context: CallbackContext):
test_type = update.message.text.strip()
context.user_data['test_type'] = test_type

if test_type == 'آيات':
surahs = ['الفاتحة', 'البقرة', 'آل عمران']  # Add more Surahs as needed
else:
surahs = ['الفاتحة', 'البقرة', 'آل عمران']  # Add more Surahs as needed

keyboard = [[surah] for surah in surahs]
reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
update.message.reply_text("📖 اختر السورة:", reply_markup=reply_markup)

def begin_quiz(update: Update, context: CallbackContext):
surah = update.message.text.strip()
test_type = context.user_data.get('test_type')

if test_type == 'آيات':
# Load questions for the selected Surah (implement filtering logic based on Surah)
aya_sample = random.sample(questions_aya, 10)  # Adjust to filter by Surah
combined = [{'type': 'aya', 'data': q} for q in aya_sample]
else:
# Load questions for the selected Surah (implement filtering logic based on Surah)
complete_sample = random.sample(questions_complete, 10)  # Adjust to filter by Surah
combined = [{'type': 'complete', 'data': q} for q in complete_sample]

random.shuffle(combined)

context.user_data['quiz'] = {
'questions': combined,
'current': 0,
'score': 0,
'start_time': time.time()
}

send_next_question(update, context)

def send_next_question(update: Update, context: CallbackContext):
quiz = context.user_data.get('quiz')
if not quiz:
update.message.reply_text("⚠️ لم يتم بدء الاختبار بعد.")
return

elapsed_time = time.time() - quiz['start_time']
remaining_seconds = int((20 * 60) - elapsed_time)

if remaining_seconds <= 0 or quiz['current'] >= 20:
finish_quiz(update, context)
return

minutes, seconds = divmod(remaining_seconds, 60)
update.message.reply_text(f"🕒 الوقت المتبقي: {minutes}:{str(seconds).zfill(2)} دقيقة")

q = quiz['questions'][quiz['current']]
context.user_data['current_question'] = q

if q['type'] == 'aya':
data = q['data']
text = data['text']
choices = [data['choice1'], data['choice2'], data['choice3'], data['choice4']]
correct_index = int(data['correct']) - 1
correct_text = choices[correct_index]
random.shuffle(choices)
new_correct_index = choices.index(correct_text)
context.user_data['expected'] = str(new_correct_index + 1)

msg = f"📖 الآية:\n{text}\n\nما الآية التالية؟\n"
for i, c in enumerate(choices, 1):
msg += f"{i}. {c}\n"
msg += "\n✏️ أرسل رقم الإجابة الصحيحة"
update.message.reply_text(msg)

else:
data = q['data']
context.user_data['expected'] = data['correct'].strip()
msg = f"✍️ أكمل الآية:\n{data['aya']}..."
update.message.reply_text(msg)

def handle_answer(update: Update, context: CallbackContext):
if context.user_data.get('awaiting_name'):
name = update.message.text.strip()
context.user_data['name'] = name
context.user_data['awaiting_name'] = False
select_test_type(update, context)
return

quiz = context.user_data.get('quiz')
expected = context.user_data.get('expected')
if not quiz or expected is None:
update.message.reply_text("❗️ أرسل /start للبدء من جديد.")
return

user_answer = update.message.text.strip()
if user_answer == expected:
update.message.reply_text("✅ إجابة صحيحة! +5 نقاط")
quiz['score'] += 5
else:
update.message.reply_text(f"❌ إجابة خاطئة.\nالإجابة الصحيحة: {expected}")

quiz['current'] += 1
send_next_question(update, context)

def finish_quiz(update: Update, context: CallbackContext):
quiz = context.user_data.get('quiz')
if not quiz:
return
name = context.user_data.get('name', 'مستخدم مجهول')
score = quiz['score']
update.message.reply_text(f"🎉 انتهى الاختبار!\n📌 الاسم: {name}\n✅ النتيجة: {score} / 100")
save_result(name, score)
context.user_data.clear()

def main():
updater = Updater(BOT_TOKEN, use_context=True)
dp = updater.dispatcher

dp.add_handler(CommandHandler('start', start))
dp.add_handler(MessageHandler(Filters.regex('^📝 ابدأ الاختبار), select_test_type))
dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_answer))

updater.start_polling()
updater.idle()

if __name__ == '__main__':
main()
