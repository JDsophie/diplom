from gale_shapley import gale_shapley, generate_data

num_students = 10
num_universities = 5
k = 2

students, universities, quotas, preferences_s, preferences_u = generate_data(
    num_students, num_universities, k
)

print("Студенты:", students)
print("Университеты:", universities)
print("Квоты:", quotas)
print("Предпочтения студентов:", preferences_s)
print("Предпочтения университетов:", preferences_u)

university_matches, student_matches, unmatched_students = gale_shapley(
    num_students, num_universities, quotas, preferences_s, preferences_u
)

print("Сопоставление университетов и студентов:")
print(university_matches)
print("Сопоставление студентов и университетов:")
print(student_matches)
print("Незачисленные студенты:")
print(unmatched_students)
