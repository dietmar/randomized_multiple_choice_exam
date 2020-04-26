import argparse
import copy
import csv
import os
import random
import subprocess
import sys

from jinja2 import Environment, FileSystemLoader

ROOTDIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
TEXDIR = 'latex'
PDFDIR = 'pdf'

def parse_error(n, filename, row):
    print('PARSE ERROR: Line %d of file "%s" seems problematic ("%s")' %
        (n, filename, str(row)))
    sys.exit(1)

def read_questions(filename):
    questions = []
    q = None
    with open(filename) as csvfile:
        csvr = csv.reader(csvfile)
        for i, row in enumerate(csvr):
            # skip empty rows (first cell empty)
            if len(row) == 0 or len(row[0]) == 0:
                continue
            elif row[0] == 'Question':
                # store current question
                if q:
                    questions.append(q)
                # start a new question
                q = {
                    'question': row[1],
                    'correct': [],
                    'wrong': [],
                }
            elif row[0] == 'Correct Answer':
                if q:
                    q['correct'].append({
                        'answer': row[1],
                        'correct': True,
                    })
                else:
                    parse_error(i+1, filename, row)
            elif row[0] == 'Wrong Answer':
                    if q:
                        q['wrong'].append({
                            'answer': row[1],
                            'correct': False,
                        })
                    else:
                        parse_error(i+1, filename, row)
            else:
                parse_error(i+1, filename, row)
        if q:
            questions.append(q)
    return questions

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--lang', default='en')
    parser.add_argument('-t', '--title', default='')
    parser.add_argument('-d', '--date', default='')
    parser.add_argument('-i', '--introtext', default='')
    parser.add_argument('-n', type=int, default=1,
        help='Number of exams to generate')
    parser.add_argument('-m', type=int, default=-1,
        help='Number of questions per exam')
    parser.add_argument('--seed', type=int, default=None, help='Random seed')
    parser.add_argument('questions_file')
    args = parser.parse_args()

    questions = read_questions(args.questions_file)
    random.seed(args.seed)

    if args.m < 1 or args.m > len(questions):
        args.m = len(questions)

    # http://eosrei.net/articles/2015/11/latex-templates-python-and-jinja2-generate-pdfs
    env = Environment(
    	block_start_string = '\BLOCK{',
    	block_end_string = '}',
    	variable_start_string = '\VAR{',
    	variable_end_string = '}',
    	comment_start_string = '\#{',
    	comment_end_string = '}',
    	line_statement_prefix = '%%',
    	line_comment_prefix = '%#',
    	trim_blocks = True,
    	autoescape = False,
        loader=FileSystemLoader(os.path.join(ROOTDIR, 'templates')),
    )
    if not os.path.exists(TEXDIR):
        os.mkdir(TEXDIR)

    if not os.path.exists(PDFDIR):
        os.mkdir(PDFDIR)

    exams = []
    for i in range(1, args.n + 1):
        shuffled = copy.deepcopy(questions)
        random.shuffle(shuffled)
        shuffled = shuffled[0:args.m]
        for j, q in enumerate(shuffled):
            q['idx'] = j + 1
            q['answers'] = q['correct'] + q['wrong']
            random.shuffle(q['answers'])
            for k, a in enumerate(q['answers']):
                if a['correct']:
                    q['correct_index'] = k + 1
                    print('question %d: correct: index %d, "%s"' % (j + 1, k + 1, a['answer']))

        # generate .tex files
        tpl = env.get_template('template_%s.tex' % args.lang)
        texfile = os.path.join(TEXDIR, 'exam_%03d.tex' % i)
        with open(texfile, 'w') as f:
            f.write(tpl.render(
                questions=shuffled,
                title=args.title,
                introtext=args.introtext,
                date=args.date,
                exam_num=i,
            ))

        # compile to PDF
        subprocess.call(['pdflatex', '-output-directory', PDFDIR, texfile])
        subprocess.call(['pdflatex', '-output-directory', PDFDIR, texfile])

        exams.append(shuffled)

    # prepare grading CSV
    tpl = env.get_template('grading.csv')
    with open('grading.csv', 'w') as f:
        f.write(tpl.render(
            exams=exams,
        ))
