from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import requests
import csv
import io
import random
import os
from datetime import datetime
import re

# إعداد المتغيرات والروابط
BOT_TOKEN = '6671455687:AAHemRdgQbmodCsqeIaha55qfPml_h9cjVQ'
CSV_URL_NEXT = 'https://docs.google.com/spreadsheets/d/1RvSq_A1HPPv4bLvby9Ez4e5vMV9_T7qVNUPHu5AX_ZQ/gviz/tq?tqx=out:csv&sheet=aya'
CSV_URL_COMPLETE = 'https://docs.google.com/spreadsheets/d/1Hlg56BLG0X_QZC_cAyIj5VMsq79Omeg6PlUW1XQfkfI/gviz/tq?tqx=out:csv&sheet=complete'
CSV_URL_ORDER = 'https://docs.google.com/spreadsheets/d/1opUbpiRngFk8tJVqt-jffAkr27kI9CwpAdd7QnOFsK4/gviz/tq?tqx=out:csv&sheet=order'

QURAN_SURAHS = [
    'الفاتحة', 'البقرة', 'آل عمران', 'النساء', 'المائدة', 'الأنعام', 'الأعراف',
    'الأنفال', 'التوبة', 'يونس', 'هود', 'يوسف', 'الرعد', 'إبراهيم', 'الحجر',
    'النحل', 'الإسراء', 'الكهف', 'مريم', 'طه', 'الأنبياء', 'الحج', 'المؤمنون',
    'النور', 'الفرقان', 'الشعراء', 'النمل', 'القصص', 'العنكبوت', 'الروم', 'لقمان',
    'السجدة', 'الأحزاب', 'سبأ', 'فاطر', 'يس', 'الصافات', 'ص', 'الزمر', 'غافر',
    'فصلت', 'الشورى', 'الزخرف', 'الدخان', 'الجاثية', 'الأحقاف', 'محمد', 'الفتح',
    'الحجرات', 'ق', 'الذاريات', 'الطور', 'النجم', 'القمر', 'الرحمن', 'الواقعة',
    'الحديد', 'المجادلة', 'الحشر', 'الممتحنة', 'الصف', 'الجمعة', 'المنافقون',
    'التغابن', 'الطلاق', 'التحريم', 'الملك', 'القلم', 'الحاقة', 'المعارج', 'نوح',
    'الجن', 'المزمل', 'المدثر', 'القيامة', 'الإنسان', 'المرسلات', 'النبأ',
    'النازعات', 'عبس', 'التكوير', 'الانفطار', 'المطففين', 'الانشقاق', 'البروج',
    'الطارق', 'الأعلى', 'الغاشية', 'الفجر', 'البلد', 'الشمس', 'الليل', 'الضحى',
    'الشرح', 'التين', 'العلق', 'القدر', 'البينة', 'الزلزلة', 'العاديات', 'القارعة',
    'التكاثر', 'العصر', 'الهمزة', 'الفيل', 'قريش', 'الماعون', 'الكوثر', 'الكافرون',
    'النصر', 'المسد', 'الإخلاص', 'الفلق', 'الناس'
]

MAX_QUESTIONS = 25

def normalize_surah_name(name):
    """تقوم بتوحيد أسماء السور بإزالة الفراغات والحركات لتحسين المطابقة"""
    if not name:
        return ""
    # إزالة جميع الفراغات والحركات والهمزات
    name = re.sub(r'[\sًٌٍَُِّٰ]+', '', name)
    # استبدال الهمزات بأشكالها الأساسية
    replacements = {
        'أ': 'ا',
        'إ': 'ا',
        'آ': 'ا',
        'ة': 'ه',
    }
    for old, new in replacements.items():
        name = name.replace(old, new)
    return name.strip()

def load_questions(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.content.decode('utf-8')
        reader = csv.DictReader(io.StringIO(data))
        return list(reader)
    except Exception as e:
        print(f"Error loading questions: {e}")
        return []

questions_next = load_questions(CSV_URL_NEXT)
questions_complete = load_questions(CSV_URL_COMPLETE)
questions_order = load_questions(CSV_URL_ORDER)

def start(update: Update, context: CallbackContext):
    update.message.reply_text("✍️ من فضلك، أدخل اسمك قبل البدء:")
    context.user_data.clear()
    context.user_data['awaiting_name'] = True

def save_result(name, score, surah, test_type):
    filename = 'results.csv'
    file_exists = os.path.isfile(filename)
    with open(filename, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(['الاسم', 'النتيجة', 'السورة', 'نوع الاختبار', 'التاريخ'])
        writer.writerow([name, score, surah, test_type, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])

def select_test_type(update: Update, context: CallbackContext):
    keyboard = [
        ['ما هي الآية التالية؟', 'إكمال الآية'],
        ['ترتيب كلمات الآية'],
        ['مزيج', 'اختبار شامل']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    update.message.reply_text("📚 اختر نوع الاختبار:", reply_markup=reply_markup)

def ask_question_count(update: Update, context: CallbackContext):
    test_type = update.message.text.strip()
    context.user_data['test_type'] = test_type
    update.message.reply_text(f"كم عدد الأسئلة التي تريدها؟ (الحد الأقصى {MAX_QUESTIONS})")
    context.user_data['awaiting_question_count'] = True

def select_surah(update: Update, context: CallbackContext):
    try:
        qcount = int(update.message.text.strip())
        if qcount < 1 or qcount > MAX_QUESTIONS:
            raise ValueError
    except Exception:
        update.message.reply_text(f"⚠️ أدخل رقمًا صحيحًا بين 1 و{MAX_QUESTIONS}.")
        return
    context.user_data['question_count'] = qcount
    context.user_data['awaiting_question_count'] = False
    surah_groups = [QURAN_SURAHS[i:i+3] for i in range(0, len(QURAN_SURAHS), 3)]
    reply_markup = ReplyKeyboardMarkup(surah_groups, resize_keyboard=True)
    update.message.reply_text("📖 اختر السورة من الأزرار فقط:", reply_markup=reply_markup)

def begin_quiz(update: Update, context: CallbackContext):
    user_input = update.message.text.strip()
    matched_surah = None
    normalized_input = normalize_surah_name(user_input)
    
    for surah in QURAN_SURAHS:
        if normalize_surah_name(surah) == normalized_input:
            matched_surah = surah
            break
    
    if not matched_surah:
        surah_groups = [QURAN_SURAHS[i:i+3] for i in range(0, len(QURAN_SURAHS), 3)]
        reply_markup = ReplyKeyboardMarkup(surah_groups, resize_keyboard=True)
        update.message.reply_text("⚠️ السورة غير معروفة. الرجاء الاختيار من القائمة.", reply_markup=reply_markup)
        return
    
    test_type = context.user_data.get('test_type')
    qcount = context.user_data.get('question_count', 10)
    
    if test_type == 'ما هي الآية التالية؟':
        available_questions = [q for q in questions_next 
                             if normalize_surah_name(q.get('surah', '').strip()) == normalize_surah_name(matched_surah)]
    elif test_type == 'إكمال الآية':
        available_questions = []
        for q in questions_complete:
            try:
                sura_name = q.get('surah', '').strip()
                if normalize_surah_name(sura_name) == normalize_surah_name(matched_surah):
                    ayacomplete = q.get('ayacomplete', '').strip()
                    correct_words = [q.get(f'correctword{i}', '').strip() for i in range(1, 6)]
                    correct_words = [w for w in correct_words if w]
                    correct_answer = ' '.join(correct_words)
                    
                    question = {
                        'type': 'complete',
                        'surah': matched_surah,
                        'ayacomplete': ayacomplete,
                        'correct': correct_answer,
                        'full_data': q
                    }
                    available_questions.append(question)
            except Exception as e:
                print(f"Error processing question: {e}")
                continue
    elif test_type == 'ترتيب كلمات الآية':
        available_questions = [q for q in questions_order 
                             if normalize_surah_name(q.get('surah', '').strip()) == normalize_surah_name(matched_surah)]
    elif test_type == 'مزيج':
        next_q = [q for q in questions_next 
                 if normalize_surah_name(q.get('surah', '').strip()) == normalize_surah_name(matched_surah)]
        complete_q = []
        for q in questions_complete:
            try:
                sura_name = q.get('surah', '').strip()
                if normalize_surah_name(sura_name) == normalize_surah_name(matched_surah):
                    ayacomplete = q.get('ayacomplete', '').strip()
                    correct_words = [q.get(f'correctword{i}', '').strip() for i in range(1, 6)]
                    correct_words = [w for w in correct_words if w]
                    correct_answer = ' '.join(correct_words)
                    
                    question = {
                        'type': 'complete',
                        'surah': matched_surah,
                        'ayacomplete': ayacomplete,
                        'correct': correct_answer,
                        'full_data': q
                    }
                    complete_q.append(question)
            except Exception as e:
                print(f"Error processing question: {e}")
                continue
        
        n = min(qcount // 2, len(next_q))
        c = min(qcount - n, len(complete_q))
        sample = []
        if n > 0:
            sample += random.sample(next_q, n)
        if c > 0:
            sample += random.sample(complete_q, c)
        random.shuffle(sample)
        available_questions = sample
    elif test_type == 'اختبار شامل':
        next_q = [q for q in questions_next 
                 if normalize_surah_name(q.get('surah', '').strip()) == normalize_surah_name(matched_surah)]
        complete_q = []
        for q in questions_complete:
            try:
                sura_name = q.get('surah', '').strip()
                if normalize_surah_name(sura_name) == normalize_surah_name(matched_surah):
                    ayacomplete = q.get('ayacomplete', '').strip()
                    correct_words = [q.get(f'correctword{i}', '').strip() for i in range(1, 6)]
                    correct_words = [w for w in correct_words if w]
                    correct_answer = ' '.join(correct_words)
                    
                    question = {
                        'type': 'complete',
                        'surah': matched_surah,
                        'ayacomplete': ayacomplete,
                        'correct': correct_answer,
                        'full_data': q
                    }
                    complete_q.append(question)
            except Exception as e:
                print(f"Error processing question: {e}")
                continue
        
        order_q = [q for q in questions_order 
                  if normalize_surah_name(q.get('surah', '').strip()) == normalize_surah_name(matched_surah)]
        
        n = min(qcount // 3, len(next_q))
        c = min(qcount // 3, len(complete_q))
        o = min(qcount - n - c, len(order_q))
        sample = []
        if n > 0:
            sample += random.sample(next_q, n)
        if c > 0:
            sample += random.sample(complete_q, c)
        if o > 0:
            sample += random.sample(order_q, o)
        random.shuffle(sample)
        available_questions = sample
    else:
        update.message.reply_text("⚠️ نوع اختبار غير مدعوم.")
        return

    if not available_questions:
        update.message.reply_text(f"⚠️ لا توجد أسئلة متاحة لسورة {matched_surah}")
        return

    selected_questions = random.sample(available_questions, min(qcount, len(available_questions)))
    context.user_data['quiz'] = {
        'questions': selected_questions,
        'current': 0,
        'score': 0,
        'surah': matched_surah,
        'test_type': test_type,
        'corrections': []
    }
    update.message.reply_text(f"بدأ اختبار {test_type} لسورة {matched_surah}", reply_markup=ReplyKeyboardRemove())
    send_next_question(update, context)

def send_next_question(update: Update, context: CallbackContext):
    quiz = context.user_data['quiz']
    idx = quiz['current']
    if idx >= len(quiz['questions']):
        return finish_quiz(update, context)
    
    q = quiz['questions'][idx]
    t = quiz['test_type']
    
    # كشف نوع السؤال في المزيج والشامل
    if t in ['مزيج', 'اختبار شامل']:
        if 'choice1' in q:
            t = 'ما هي الآية التالية؟'
        elif 'ayacomplete' in q:
            t = 'إكمال الآية'
        elif 'k1' in q:
            t = 'ترتيب كلمات الآية'

    if t == 'ما هي الآية التالية؟':
        msg = f"📖 الآية:\n{q['text']}\n\nما الآية التالية؟"
        choices = [q['choice1'], q['choice2'], q['choice3'], q['choice4']]
        correct_answer = choices[int(q['correct']) - 1]
        zipped = list(enumerate(choices, 1))
        random.shuffle(zipped)
        for idx2, (num, choice) in enumerate(zipped):
            if choice == correct_answer:
                correct_number = idx2 + 1
        context.user_data['correct_answer'] = str(correct_number)
        context.user_data['correction_data'] = {
            'type': t,
            'question': q['text'],
            'correct': correct_answer,
            'choices': [choice for _, choice in zipped]
        }
        keyboard = [[str(i)] for i in range(1, 5)]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        for i, (num, choice) in enumerate(zipped, 1):
            msg += f"\n{i}. {choice}"
        update.message.reply_text(msg, reply_markup=reply_markup)
        context.user_data['order_mode'] = False
    elif t == 'إكمال الآية':
        msg = f"✍️ أكمل الآية:\n{q['ayacomplete']} ..."
        context.user_data['correct_answer'] = q['correct']
        context.user_data['correction_data'] = {
            'type': t,
            'question': q['ayacomplete'],
            'correct': q['correct']
        }
        update.message.reply_text(msg, reply_markup=ReplyKeyboardRemove())
        context.user_data['order_mode'] = False
    elif t == 'ترتيب كلمات الآية':
        words = [q.get(f'k{i}') for i in range(1, 13) if q.get(f'k{i}') and q.get(f'k{i}').strip()]
        correct = words
        shuffled = words[:]
        random.shuffle(shuffled)
        msg = f"🔀 رتب الكلمات التالية لتكوين الآية:\n"
        for idx3, w in enumerate(shuffled, 1):
            msg += f"{idx3}. {w}\n"
        msg += "\n✏️ أرسل الترتيب الصحيح بالأرقام (مثال: 2 1 3 4 ...)"
        context.user_data['order_words'] = shuffled
        context.user_data['correct_order'] = correct
        context.user_data['correction_data'] = {
            'type': t,
            'question': ' '.join(shuffled),
            'correct': ' '.join(correct)
        }
        context.user_data['order_mode'] = True
        update.message.reply_text(msg, reply_markup=ReplyKeyboardRemove())
    else:
        update.message.reply_text("⚠️ نوع سؤال غير مدعوم.")
        quiz['current'] += 1
        send_next_question(update, context)

def handle_answer(update: Update, context: CallbackContext):
    if context.user_data.get('awaiting_name'):
        name = update.message.text.strip()
        if len(name) < 2:
            update.message.reply_text("⚠️ الاسم قصير جداً. الرجاء إدخال اسم صحيح.")
            return
        context.user_data['name'] = name
        context.user_data['awaiting_name'] = False
        return select_test_type(update, context)
    if context.user_data.get('awaiting_question_count'):
        return select_surah(update, context)
    if 'quiz' not in context.user_data:
        update.message.reply_text("❗️ الجلسة انتهت. أرسل /start للبدء من جديد.")
        return

    quiz = context.user_data['quiz']
    idx = quiz['current']
    if idx >= len(quiz['questions']):
        return finish_quiz(update, context)
    
    user_answer = update.message.text.strip()
    correction_data = context.user_data.get('correction_data', {})
    
    if context.user_data.get('order_mode'):
        try:
            indices = [int(x)-1 for x in user_answer.split()]
            words = context.user_data['order_words']
            user_order = [words[i] for i in indices]
            correct = context.user_data['correct_order']
            if user_order == correct:
                update.message.reply_text("✅ ترتيب صحيح! +5 نقاط")
                quiz['score'] += 5
            else:
                update.message.reply_text(f"❌ ترتيب خاطئ. الترتيب الصحيح:\n{' '.join(correct)}")
                quiz['corrections'].append({
                    'type': correction_data.get('type', 'ترتيب كلمات الآية'),
                    'question': correction_data.get('question', ''),
                    'your_answer': ' '.join(user_order),
                    'correct': correction_data.get('correct', '')
                })
        except Exception:
            update.message.reply_text("⚠️ صيغة غير صحيحة. أرسل أرقام الترتيب مفصولة بمسافة.")
            return
        context.user_data['order_mode'] = False
    else:
        correct_answer = context.user_data.get('correct_answer')
        if correct_answer is None:
            update.message.reply_text("⚠️ خطأ في النظام. الرجاء البدء من جديد.")
            return start(update, context)
        
        # مقارنة مرنة للإجابة
        if quiz['test_type'] == 'إكمال الآية':
            is_correct = normalize_surah_name(user_answer) == normalize_surah_name(correct_answer)
        else:
            is_correct = user_answer == correct_answer
            
        if is_correct:
            update.message.reply_text("✅ إجابة صحيحة! +5 نقاط")
            quiz['score'] += 5
        else:
            update.message.reply_text(f"❌ إجابة خاطئة. الإجابة الصحيحة هي: {correct_answer}")
            quiz['corrections'].append({
                'type': correction_data.get('type', ''),
                'question': correction_data.get('question', ''),
                'your_answer': user_answer,
                'correct': correction_data.get('correct', '')
            })
    
    quiz['current'] += 1
    send_next_question(update, context)

def finish_quiz(update: Update, context: CallbackContext):
    quiz = context.user_data.get('quiz')
    if not quiz:
        update.message.reply_text("❗️ الجلسة انتهت. أرسل /start للبدء من جديد.")
        return
    
    name = context.user_data.get('name', 'مجهول')
    score = quiz['score']
    max_score = len(quiz['questions']) * 5
    percentage = (score / max_score) * 100 if max_score > 0 else 0
    
    result_msg = (
        f"🎉 انتهى الاختبار!\n"
        f"📌 الاسم: {name}\n"
        f"📖 السورة: {quiz['surah']}\n"
        f"📝 نوع الاختبار: {quiz['test_type']}\n"
        f"✅ النتيجة: {score}/{max_score}\n"
        f"📊 النسبة: {percentage:.1f}%"
    )
    update.message.reply_text(result_msg)
    
    # عرض التصحيحات
    if quiz['corrections']:
        msg = "❌ الأسئلة الخاطئة وتصحيحاتها:\n"
        for i, c in enumerate(quiz['corrections'], 1):
            msg += f"\n{i}. [{c['type']}]\nس: {c['question']}\nإجابتك: {c['your_answer']}\nالصحيح: {c['correct']}\n"
        update.message.reply_text(msg)
    
    save_result(name, score, quiz['surah'], quiz['test_type'])
    context.user_data.clear()

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(MessageHandler(Filters.regex('^(ما هي الآية التالية؟|إكمال الآية|ترتيب كلمات الآية|مزيج|اختبار شامل)$'), ask_question_count))
    dp.add_handler(MessageHandler(Filters.regex('^\d+$'), handle_answer))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, begin_quiz))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_answer))
    
    updater.start_polling()
    print("Bot is running...")
    updater.idle()

if __name__ == "__main__":
    main()
