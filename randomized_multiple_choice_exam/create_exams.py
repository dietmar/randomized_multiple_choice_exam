import argparse
import csv
import random
import sys

from jinja2 import Environment, FileSystemLoader

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
            if len(row[0]) == 0:
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
                    q['correct'].append(row[1])
                else:
                    parse_error(i+1, filename, row)
            elif row[0] == 'Wrong Answer':
                    if q:
                        q['wrong'].append(row[1])
                    else:
                        parse_error(i+1, filename, row)
            else:
                parse_error(i+1, filename, row)
    return questions

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', help='Number of exams to generate')
    parser.add_argument('--seed', type=int, default=None, help='Random seed')
    parser.add_argument('questions_file')
    args = parser.parse_args()

    questions = read_questions(args.questions_file)
    random.seed(args.seed)

    shuffled = questions[:]
    random.shuffle(shuffled)
    for i, q in enumerate(shuffled):
        q['idx'] = i + 1
        q['answers'] = q['correct'] + q['wrong']
        random.shuffle(q['answers'])

    env = Environment(
        loader=FileSystemLoader('templates'),
    )
    tpl = env.get_template('template.tex')
    print(tpl.render(questions=shuffled))
