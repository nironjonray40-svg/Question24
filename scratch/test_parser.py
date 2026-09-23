# -*- coding: utf-8 -*-
import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

test_text = """
[সৃজনশীল ১]
১। নিচের অনুচ্ছেদটি পড়ে সংশ্লিষ্ট প্রশ্নগুলোর উত্তর দাও:
দশম শ্রেণির ছাত্রী মিতু চোখে দেখে না। কিন্তু তার স্মৃতিশক্তি প্রখর এবং গানের গলা চমৎকার। পরিবারের সদস্যরা তাকে নিয়ে লজ্জিত না হয়ে তার সংগীত চর্চায় সর্বাত্মক সহায়তা করেন। ফলে মিতু জাতীয় পর্যায়ে শ্রেষ্ঠ সংগীতশিল্পী হিসেবে পুরস্কার অর্জন করে।
(ক) সুভার পিতার নাম কী? [১]
(খ) ‘সুভার একটি বিশেষ সুবিধা ছিল’—কথাটি দ্বারা কী বোঝানো হয়েছে? [২]
(গ) উদ্দীপকের মিতুর পারিবারিক পরিবেশ ‘সুভা’ গল্পের কোন ভিন্ন দিকটি উন্মোচন করে? ব্যাখ্যা কর। [৩]
(ঘ) “মিতু অনুকূল পরিবেশ পেলেও সুভা তা থেকে বঞ্চিত ছিল”—মন্তব্যটি ‘সুভা’ গল্পের আলোকে বিশ্লেষণ কর। [৪]
উত্তর: ক) বাণীকণ্ঠ। খ) বাকপ্রতিবন্ধী হওয়ায় সাধারণ মানুষের চেয়ে প্রকৃতির সাথে নিবিড় সখ্য।

২. নিচের কোন রচনাটি আলাদা শ্রেণির? [কু. বো.'২০২৩]
(ক) বই পড়া (খ) মমতাদি (গ) নিমগাছ (ঘ) সুভা
সঠিক উত্তর: ক
ব্যাখ্যা: 'বই পড়া' একটি প্রবন্ধ, বাকিগুলো ছোটগল্প বা গল্প।

৩. বাংলা ভাষার জন্ম কোন প্রাকৃত থেকে?
ক) মাগধী
খ) শৌরসেনী
গ) মহারাষ্ট্রী
ঘ) পৈশাচী
উত্তর: ক

৪. সুভার মা কেন সুভাকে নিজের গর্ভের কলঙ্ক মনে করতেন?
উত্তর: সাধারণত মায়েরা মেয়ের মধ্যে নিজের প্রতিচ্ছবি দেখতে চান। সুভা বাকপ্রতিবন্ধী হওয়ায় মা তাকে নিজের দুর্ভাগ্যের প্রতীক মনে করতেন।
"""

def parse_structured_text_questions(raw_text):
    questions = []
    text = raw_text.replace('\r\n', '\n').replace('\r', '\n').strip()
    if not text:
        return []

    # Merge bracket header with following question number: e.g. "[সৃজনশীল ১]\n১।" -> "[সৃজনশীল ১] "
    text = re.sub(r'(\[(?:সৃজনশীল|বহুনির্বাচনি|নৈর্ব্যক্তিক|সংক্ষিপ্ত|প্রশ্ন)?\s*[\d০-৯a-zA-Z]+\])\s*\n+\s*([\d০-৯]+\s*[\.\।\)\-])', r'\1 \2', text)

    # Check if text already has distinct blocks via triple newlines
    blocks = [b.strip() for b in text.split('\n\n\n') if b.strip()]
    if len(blocks) <= 1:
        # Split on question boundaries
        pattern = r'\n(?=(?:\[(?:সৃজনশীল|বহুনির্বাচনি|নৈর্ব্যক্তিক|সংক্ষিপ্ত|প্রশ্ন)?\s*[\d০-৯a-zA-Z]+\]|^সৃজনশীল\s*(?:প্রশ্ন)?\s*[\d০-৯]+|^বহুনির্বাচনি\s*(?:প্রশ্ন)?\s*[\d০-৯]+|^সংক্ষিপ্ত\s*(?:প্রশ্ন)?\s*[\d০-৯]+|^[\d০-৯]+\s*[\.\।\)\-]\s+|^প্রশ্ন\s*[\d০-৯]*\s*[:\-]))'
        blocks = [b.strip() for b in re.split(pattern, text, flags=re.MULTILINE) if b.strip()]
    
    if len(blocks) <= 1:
        # Fallback split by double newlines
        double_split = [b.strip() for b in text.split('\n\n') if b.strip()]
        if len(double_split) > 1:
            blocks = double_split

    ans_map = {'a': 'ক', 'b': 'খ', 'c': 'গ', 'd': 'ঘ', '1': 'ক', '2': 'খ', '3': 'গ', '4': 'ঘ', 'ক': 'ক', 'খ': 'খ', 'গ': 'গ', 'ঘ': 'ঘ'}

    for block in blocks:
        lines = [l.strip() for l in block.split('\n') if l.strip()]
        if not lines:
            continue
            
        block_text = '\n'.join(lines)
        
        # Check answer indicator with a single letter (indicates MCQ)
        m_ans_single = re.search(r'(?:সঠিক\s*উত্তর|উত্তর|Ans|উত্তরঃ|সঠিক)\s*[:\-]\s*[\(\[]?([কখগঘabcdABCD1234])[\)\]]?(?:\s|$|\.|\;|\n)', block_text)
        
        has_cq_explicit = any(k in block_text for k in ['[সৃজনশীল', 'সৃজনশীল প্রশ্ন', 'উদ্দীপক:', 'উদ্দীপক -', 'দৃশ্যকল্প:'])
        has_sub_ka = bool(re.search(r'(?:^|\n)\s*(?:ক\)|ক\.|\(ক\)|ক\s*[:\-])', block_text))
        has_sub_kha = bool(re.search(r'(?:^|\n)\s*(?:খ\)|খ\.|\(খ\)|খ\s*[:\-])', block_text))
        has_sub_ga = bool(re.search(r'(?:^|\n)\s*(?:গ\)|গ\.|\(গ\)|গ\s*[:\-])', block_text))
        has_sub_gha = bool(re.search(r'(?:^|\n)\s*(?:ঘ\)|ঘ\.|\(ঘ\)|ঘ\s*[:\-])', block_text))

        # Distinct CQ check: must have explicit CQ keywords OR (sub ka, kha, ga, gha AND NO single-letter MCQ answer)
        is_cq = (has_cq_explicit and has_sub_ka and has_sub_kha) or (has_sub_ka and has_sub_kha and has_sub_ga and has_sub_gha and not m_ans_single)
        
        # Distinct MCQ check: has options and either answer or single-line 4 options or explicit mcq tag
        has_mcq_options = bool(re.search(r'[\(\[]?[কA1][\)\]\.\-:]', block_text)) and bool(re.search(r'[\(\[]?[খB2][\)\]\.\-:]', block_text))
        is_mcq = not is_cq and has_mcq_options

        
        if is_cq:
            stem = ""
            ka, kha, ga, gha, sol = "", "", "", "", ""
            current_field = 'stem'
            
            for line in lines:
                # Strip bracket headers like [সৃজনশীল ১] or [১]
                if re.match(r'^\[(?:সৃজনশীল|প্রশ্ন)?\s*[\d০-৯a-zA-Z]+\]$', line):
                    continue
                # Also strip standalone question numbers at the start of line like "১। " or "১. "
                clean_line = re.sub(r'^(?:সৃজনশীল\s*(?:প্রশ্ন)?\s*[\d০-৯]+[:\.\-]?\s*|[\d০-৯]+\s*[\.\।\)\-]\s+)', '', line).strip()
                
                m_ka = re.match(r'^(?:ক\)|ক\.|\(ক\)|ক\s*[:\-])\s*(.*)', clean_line)
                m_kha = re.match(r'^(?:খ\)|খ\.|\(খ\)|খ\s*[:\-])\s*(.*)', clean_line)
                m_ga = re.match(r'^(?:গ\)|গ\.|\(গ\)|গ\s*[:\-])\s*(.*)', clean_line)
                m_gha = re.match(r'^(?:ঘ\)|ঘ\.|\(ঘ\)|ঘ\s*[:\-])\s*(.*)', clean_line)
                m_sol = re.match(r'^(?:সমাধান|উত্তর|নির্দেশনা|Ans)\s*[:\-]\s*(.*)', clean_line)
                m_stem = re.match(r'^(?:উদ্দীপক|দৃশ্যকল্প|অনুচ্ছেদ)\s*[:\-]\s*(.*)', clean_line)
                
                if m_stem:
                    current_field = 'stem'
                    val = m_stem.group(1).strip()
                    if val:
                        stem += val + "\n"
                elif m_ka:
                    current_field = 'ka'
                    ka = re.sub(r'\s*\[[\d০-৯]+\]$', '', m_ka.group(1)).strip()
                elif m_kha:
                    current_field = 'kha'
                    kha = re.sub(r'\s*\[[\d০-৯]+\]$', '', m_kha.group(1)).strip()
                elif m_ga:
                    current_field = 'ga'
                    ga = re.sub(r'\s*\[[\d০-৯]+\]$', '', m_ga.group(1)).strip()
                elif m_gha:
                    current_field = 'gha'
                    gha = re.sub(r'\s*\[[\d০-৯]+\]$', '', m_gha.group(1)).strip()
                elif m_sol:
                    current_field = 'sol'
                    sol += m_sol.group(1).strip() + "\n"
                else:
                    if current_field == 'stem':
                        stem += clean_line + "\n"
                    elif current_field == 'ka':
                        ka += " " + clean_line
                    elif current_field == 'kha':
                        kha += " " + clean_line
                    elif current_field == 'ga':
                        ga += " " + clean_line
                    elif current_field == 'gha':
                        gha += " " + clean_line
                    elif current_field == 'sol':
                        sol += clean_line + "\n"
            
            # Clean marks markers e.g. [১], [২], [৩], [৪]
            ka = re.sub(r'\s*\[[\d০-৯]+\]$', '', ka).strip()
            kha = re.sub(r'\s*\[[\d০-৯]+\]$', '', kha).strip()
            ga = re.sub(r'\s*\[[\d০-৯]+\]$', '', ga).strip()
            gha = re.sub(r'\s*\[[\d০-৯]+\]$', '', gha).strip()
            
            questions.append({
                'type': 'cq',
                'question_type': 'cq',
                'cq_stem': stem.strip(),
                'cq_sub_ka': ka.strip(),
                'cq_sub_kha': kha.strip(),
                'cq_sub_ga': ga.strip(),
                'cq_sub_gha': gha.strip(),
                'cq_solution': sol.strip(),
                'marks': 10.0,
                'difficulty': 'medium'
            })
            continue

        # 2. CHECK IF MCQ (বহুনির্বাচনি)
        # Check if single line has all 4 options: (ক) ... (খ) ... (গ) ... (ঘ) ...
        # Or multiple lines have ক), খ), গ), ঘ)
        has_mcq_options = bool(re.search(r'[\(\[]?[কA1][\)\]\.\-:]', block_text)) and bool(re.search(r'[\(\[]?[খB2][\)\]\.\-:]', block_text))
        
        if is_mcq:
            q_stem = ""
            opt_a, opt_b, opt_c, opt_d = "", "", "", ""
            ans, exp = "", ""
            
            stem_lines = []
            
            for line in lines:
                if re.match(r'^\[(?:বহুনির্বাচনি|নৈর্ব্যক্তিক|প্রশ্ন)?\s*[\d০-৯a-zA-Z]+\]$', line):
                    continue
                    
                # Answer line?
                m_ans = re.search(r'(?:সঠিক\s*উত্তর|উত্তর|Ans|উত্তরঃ|সঠিক)\s*[:\-]\s*[\(\[]?([কখগঘabcdABCD1234])[\)\]]?', line)
                if m_ans:
                    raw_a = m_ans.group(1).lower()
                    ans = ans_map.get(raw_a, raw_a)
                    # Check if line also has explanation
                    if 'ব্যাখ্যা' in line:
                        exp_part = line.split('ব্যাখ্যা', 1)[-1].lstrip(':- ')
                        if exp_part:
                            exp = exp_part.strip()
                    continue
                
                # Explanation line?
                m_exp = re.search(r'(?:ব্যাখ্যা|Exp(?:lanation)?)\s*[:\-]\s*(.*)', line)
                if m_exp:
                    exp = m_exp.group(1).strip()
                    continue
                
                # Check for 4 options in a single line
                m_4opts = re.search(
                    r'[\(\[]?([কA1a])[\]\)\.\-:]\s*(.*?)\s+[\(\[]?([খB2b])[\]\)\.\-:]\s*(.*?)\s+[\(\[]?([গC3c])[\]\)\.\-:]\s*(.*?)\s+[\(\[]?([ঘD4d])[\]\)\.\-:]\s*(.*)',
                    line
                )
                if m_4opts:
                    opt_a = m_4opts.group(2).strip()
                    opt_b = m_4opts.group(4).strip()
                    opt_c = m_4opts.group(6).strip()
                    opt_d = m_4opts.group(8).strip()
                    # If opt_d contains trailing answer e.g. "সুভা  উত্তর: ক"
                    if any(k in opt_d for k in ['উত্তর:', 'Ans:', 'সঠিক উত্তর:']):
                        parts = re.split(r'(?:সঠিক\s*উত্তর|উত্তর|Ans|উত্তরঃ)\s*[:\-]', opt_d, 1)
                        opt_d = parts[0].strip()
                        if len(parts) > 1:
                            m_sub_ans = re.search(r'[\(\[]?([কখগঘabcdABCD1234])[\)\]]?', parts[1])
                            if m_sub_ans:
                                ans = ans_map.get(m_sub_ans.group(1).lower(), m_sub_ans.group(1))
                    continue
                
                # Check for 2 options in a single line: (ক) ... (খ) ...
                m_2opts_ab = re.search(r'[\(\[]?([কA1a])[\]\)\.\-:]\s*(.*?)\s+[\(\[]?([খB2b])[\]\)\.\-:]\s*(.*)', line)
                if m_2opts_ab:
                    opt_a = m_2opts_ab.group(2).strip()
                    opt_b = m_2opts_ab.group(4).strip()
                    continue
                # (গ) ... (ঘ) ...
                m_2opts_cd = re.search(r'[\(\[]?([গC3c])[\]\)\.\-:]\s*(.*?)\s+[\(\[]?([ঘD4d])[\]\)\.\-:]\s*(.*)', line)
                if m_2opts_cd:
                    opt_c = m_2opts_cd.group(2).strip()
                    opt_d = m_2opts_cd.group(4).strip()
                    continue
                
                # Check single option per line
                m_opt_a = re.match(r'^(?:ক\)|ক\.|\(ক\)|ক\s*[:\-]|\(A\)|A\)|A\.)\s*(.*)', line)
                m_opt_b = re.match(r'^(?:খ\)|খ\.|\(খ\)|খ\s*[:\-]|\(B\)|B\)|B\.)\s*(.*)', line)
                m_opt_c = re.match(r'^(?:গ\)|গ\.|\(গ\)|গ\s*[:\-]|\(C\)|C\)|C\.)\s*(.*)', line)
                m_opt_d = re.match(r'^(?:ঘ\)|ঘ\.|\(ঘ\)|ঘ\s*[:\-]|\(D\)|D\)|D\.)\s*(.*)', line)
                
                if m_opt_a:
                    opt_a = m_opt_a.group(1).strip()
                elif m_opt_b:
                    opt_b = m_opt_b.group(1).strip()
                elif m_opt_c:
                    opt_c = m_opt_c.group(1).strip()
                elif m_opt_d:
                    opt_d = m_opt_d.group(1).strip()
                else:
                    # Line belongs to question stem
                    clean_line = re.sub(r'^(?:প্রশ্ন\s*[\d০-৯]*\s*[:\.\-]?\s*|Q\s*[\d০-৯]*\s*[:\.\-]?\s*|[\d০-৯]+\s*[\.\।\)\-]\s+)', '', line).strip()
                    stem_lines.append(clean_line)
            
            q_stem = ' '.join(stem_lines).strip()
            
            questions.append({
                'type': 'mcq',
                'question_type': 'mcq',
                'mcq_stem': q_stem,
                'option_a': opt_a,
                'option_b': opt_b,
                'option_c': opt_c,
                'option_d': opt_d,
                'correct_option': ans,
                'explanation': exp,
                'marks': 1.0,
                'difficulty': 'medium'
            })
            continue

        # 3. SHORT QUESTION (সংক্ষিপ্ত প্রশ্ন)
        q_lines = []
        a_lines = []
        is_ans = False
        
        for line in lines:
            if re.match(r'^\[(?:সংক্ষিপ্ত|প্রশ্ন)?\s*[\d০-৯a-zA-Z]+\]$', line):
                continue
            m_a = re.match(r'^(?:উত্তর|সমাধান|Ans|উত্তরঃ)\s*[:\-]\s*(.*)', line)
            if m_a:
                is_ans = True
                val = m_a.group(1).strip()
                if val:
                    a_lines.append(val)
            elif is_ans:
                a_lines.append(line)
            else:
                clean_line = re.sub(r'^(?:প্রশ্ন\s*[\d০-৯]*\s*[:\.\-]?\s*|Q\s*[\d০-৯]*\s*[:\.\-]?\s*|[\d০-৯]+\s*[\.\।\)\-]\s+)', '', line).strip()
                q_lines.append(clean_line)
                
        q_text = ' '.join(q_lines).strip()
        a_text = '\n'.join(a_lines).strip()
        
        if q_text:
            questions.append({
                'type': 'short',
                'question_type': 'short',
                'short_question': q_text,
                'short_answer': a_text,
                'marks': 2.0,
                'difficulty': 'medium'
            })

    return questions

res = parse_structured_text_questions(test_text)
print(f"Total parsed: {len(res)}")
for i, q in enumerate(res):
    print(f"\n--- Question {i+1} ({q['question_type']}) ---")
    if q['question_type'] == 'cq':
        print("Stem:", q['cq_stem'][:60], "...")
        print("Ka:", q['cq_sub_ka'])
        print("Kha:", q['cq_sub_kha'])
        print("Ga:", q['cq_sub_ga'])
        print("Gha:", q['cq_sub_gha'])
    elif q['question_type'] == 'mcq':
        print("Stem:", q['mcq_stem'])
        print("A:", q['option_a'], "| B:", q['option_b'], "| C:", q['option_c'], "| D:", q['option_d'])
        print("Correct:", q['correct_option'], "| Exp:", q['explanation'])
    else:
        print("Short Q:", q['short_question'])
        print("Short Ans:", q['short_answer'])

