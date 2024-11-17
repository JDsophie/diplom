import random


def generate_data(num_students, num_universities, k):
    students = list(range(num_students))
    universities = list(range(num_universities))

    total_quotas = int(k * num_students)

    # Генерируем минимальную квоту для каждого университета и вычитаем общее количество студентов,
    # уже выделенных в минимальной квоте, чтобы понять, сколько студентов еще нужно распределить
    min_quota_per_university = 1
    remaining_students = total_quotas - (min_quota_per_university * num_universities)

    # Создаем список квот, начиная с минимального числа для каждого университета
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
    free_students = list(range(num_students))
    proposed = {student: 0 for student in range(num_students)}  # Счетчик предложений
    university_matches = {
        uni: [] for uni in range(num_universities)
    }  # Сопоставления университетов
    student_matches = {
        student: None for student in range(num_students)
    }  # Сопоставления студентов

    while free_students:
        # Вытаскиваем свободного студента
        student = free_students[0]
        student_pref = preferences_s[student]

        # Находим наиболее предпочтительный университет, которому студент еще не делал предложение
        uni_index = proposed[student]

        if uni_index < num_universities:
            uni = student_pref[uni_index]
            proposed[student] += 1

            # Если университет свободен, совмещаем
            if len(university_matches[uni]) < quotas[uni]:
                university_matches[uni].append(student)
                university_matches[uni].sort(key=preferences_u[uni].index)
                student_matches[student] = uni
                free_students.pop(0)
            else:
                # Если университет занят, проверяем, хочет ли он заменить текущего худшего студента
                current_student = university_matches[uni][-1]
                uni_pref = preferences_u[uni]

                if uni_pref.index(student) < uni_pref.index(current_student):
                    university_matches[uni].pop()
                    university_matches[uni].append(student)
                    university_matches[uni].sort(key=uni_pref.index)
                    student_matches[student] = uni
                    student_matches[current_student] = None
                    free_students.pop(0)
                    free_students.append(current_student)
        else:
            # Если студент сделал все предложения, он становится несопоставленным
            free_students.pop(0)

    unmatched_students = [s for s in range(num_students) if student_matches[s] is None]

    return university_matches, student_matches, unmatched_students
