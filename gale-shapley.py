import random
def generate_data(num_students, num_universities, k):

    students = list(range(num_students))
    universities = list(range(num_universities))

    totalquotas = int(k * num_students)
    
    # генерируем минимальную квоту для каждого университета и вычитаем общее количество студентов, уже выделенных в минимальной квоте, чтобы понять, сколько студентов еще нужно распределить
    min_quota_per_university = 1
    remaining_students = totalquotas - (min_quota_per_university * num_universities)

    #создаем список квот, начиная с минимального числа для каждого университета
    quotas = [min_quota_per_university for _ in range(num_universities)]

    # Генерируем оставшиеся квоты случайным образом
    for _ in range(remaining_students):
        index = random.randint(0, num_universities - 1)
        quotas[index] += 1

    preferences_s = {}
    preferences_u = {}
    for student in students:
        preferences_s[student] = random.sample(universities, k=num_universities)
    for uni in universities:
        preferences_u[uni] = random.sample(students, k=num_students)
    return students, universities, quotas, preferences_s, preferences_u
def gale_shapley(num_students, num_universities, quotas, preferences_s, preferences_u):
    # Инициализация
    freestudents = list(range(num_students))
    proposed = {student: 0 for student in range(num_students)}  # Счетчик предложений
    matches = {uni: [] for uni in range(num_universities)}  # Сопоставления университетов
    student_matches = {student: None for student in range(num_students)}  # Сопоставления студентов

    while freestudents:
        # Вытаскиваем свободного студента
        student = freestudents[0]
        studentpref = preferences_s[student]

        # Находим университет, которому студент еще не делал предложение
        uniindex = proposed[student]

        if uniindex < num_universities:
            uni = studentpref[uniindex]
            proposed[student] += 1

            # Если университет свободен, совмещаем
            if len(matches[uni]) < quotas[uni]:
                matches[uni].append(student)
                student_matches[student] = uni
                freestudents.remove(student)
            else:
                # Если университет занят, проверяем, хочет ли он заменить текущего студента
                currentstudent = sorted(matches[uni], key=lambda s: preferences_u[uni].index(s))[-1]
                unipref = preferences_u[uni]

                if unipref.index(student) < unipref.index(currentstudent):
                    matches[uni].remove(currentstudent)
                    matches[uni].append(student)
                    student_matches[student] = uni
                    student_matches[currentstudent] = None
                    freestudents.append(currentstudent)
                    freestudents.remove(student)
        else:
            # Если студент сделал все предложения, он становится несопоставленным
            freestudents.remove(student)

    unmatchedstudents = [s for s in range(num_students) if student_matches[s] is None]

    return matches, student_matches, unmatchedstudents