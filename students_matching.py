import random
import pandas as pd
import numpy as np

from collections import Counter

class StudentsMatching:
    def __init__(self, num_students, num_profiles, perc_of_target,
                 perc_of_contract, debts_limit, first_pref, first_pref_target,
                 min_num_groups, max_num_groups, min_group_sizes, max_group_sizes):
        self.num_students = num_students
        self.num_profiles = num_profiles
        self.perc_of_target = perc_of_target
        self.perc_of_contract = perc_of_contract
        self.debts_limit = debts_limit
        self.first_pref = first_pref
        self.first_pref_target = first_pref_target
        self.min_num_groups = min_num_groups
        self.max_num_groups = max_num_groups
        self.min_group_sizes = min_group_sizes
        self.max_group_sizes = max_group_sizes
        
        self.data_s = pd.DataFrame(index=list(range(self.num_students)))
        self.data_p = pd.DataFrame(index=list(range(self.num_profiles)))
        
        self.mandatory_profiles = None
        self.priorities = None
        self.priorities_target = None
        self.reserve_size = None
        self.reserve_students = None
        self.sorted_students = None
        self.indifferent_students = None
        self.unmatched_students = None
        self.prof_status = None
        self.a = 0
        self.current_prof_status = [None for item in range(self.data_p.shape[0])]
        
        self.profiles_matches = {prof: [] for prof in range(self.num_profiles)}
        self.student_matches = {student: None for student in range(self.num_students)}

        self.generate_profiles()    
                     
    def generate_student_labels(self):
        num_target_students = int(self.perc_of_target * self.num_students)
        self.data_s['target'] = 0
        rand_ind = np.random.choice(self.data_s.index, size=num_target_students, replace=False)
        self.data_s.loc[rand_ind, 'target'] = 1
        
        num_contract_students = int(self.perc_of_contract * self.num_students)
        self.data_s['contract'] = 0
        rand_ind = np.random.choice(self.data_s.index, size=num_contract_students, replace=False)
        self.data_s.loc[rand_ind, 'contract'] = 1

    def generate_debts(self):
        def generate_single_debt():
            return random.choices(range(8), weights=[10, 5, 3, 3, 2, 2, 1, 1], k=1)[0]

        self.data_s['debts'] = [generate_single_debt() for _ in self.data_s.index]

    def generate_rating(self):
        self.data_s['rating'] = [random.randint(0, 500) for _ in self.data_s.index]
    
    def generate_profiles(self):
        self.data_p['min_num_groups'] = self.min_num_groups
        self.data_p['max_num_groups'] = self.max_num_groups
        self.data_p['min_group_size'] = self.min_group_sizes
        self.data_p['max_group_size'] = self.max_group_sizes
        self.data_p['quota'] = self.data_p['max_group_size'] * self.data_p['max_num_groups']
        
    def generate_student_preferences(self):
        preferences_s = {}
        for student in self.data_s.index:
            if (self.data_s['debts'][student] > self.debts_limit) & (self.data_s['target'][student] == 0):
                preferences_s[student] = []
            else:
                preferences_s[student] = random.sample(list(self.data_p.index), k=self.num_profiles)
        self.data_s['preferences'] = self.data_s.index.map(preferences_s)
        
    def generate_profile_preferences(self):
        self.sorted_students = self.data_s.sort_values(by=['target', 'debts', 'rating', 'contract'], ascending=[False, True, False, False]).index.tolist()
        self.data_p['preferences'] = [self.sorted_students] * len(self.data_p)
    
    def calculate_mandatory_profiles(self):
        self.priorities = Counter([x[0] for x in self.data_s['preferences'] if x])
        self.priorities_target = Counter([x[0] for x in self.data_s[self.data_s['target'] == 1]['preferences'] if x])
        self.mandatory_profiles = list(set(
            [profile for profile, count in self.priorities.items() if count > self.first_pref] +
            [profile for profile, count in self.priorities_target.items() if count > self.first_pref_target]
        ))
        self.data_p.loc[(self.data_p.index.isin(self.mandatory_profiles)) & (self.data_p['min_num_groups'] == 0), 'min_num_groups'] = 1
        self.data_p['min_quota'] = self.data_p['min_group_size'] * self.data_p['min_num_groups']
        num_mandatory_profiles = len(self.mandatory_profiles)
        
    def calculate_reserve_size(self):
        return (self.data_p['min_group_size'] * self.data_p['min_num_groups']).sum() 
    
    def fill_reserve(self):
        self.reserve_size = self.calculate_reserve_size()
        self.indifferent_students = self.data_s[self.data_s['preferences'].apply(lambda x: not x)].index.tolist()
        indifferent_students_size = len(self.indifferent_students)
        if indifferent_students_size >= self.reserve_size:
            self.reserve_students = []
        else:
            self.reserve_students = [s for s in self.sorted_students if s not in self.indifferent_students][-(self.reserve_size-indifferent_students_size):]
    
    def gale_shapley(self, data):
        free_students = [s for s in data if s not in self.reserve_students]  
        proposed = {student: 0 for student in range(self.num_students)}
        while free_students:
            student = free_students[0]
            student_pref = self.data_s.loc[student, 'preferences']
            prof_index = proposed[student]
            if prof_index < len(student_pref):  
                prof = student_pref[prof_index]
                proposed[student] += 1
                if len(self.profiles_matches[prof]) < self.data_p['quota'][prof]:
                    self.profiles_matches[prof].append(student)
                    self.student_matches[student] = prof
                    free_students.pop(0)
                    if prof in self.mandatory_profiles and self.reserve_students and len(self.profiles_matches[prof]) < self.data_p['min_quota'][prof]:
                        student_from_reserve = self.reserve_students.pop()
                        free_students.append(student_from_reserve)
                else:
                    current_student = self.profiles_matches[prof][-1]
                    prof_pref = self.data_p['preferences'][prof]
                    if prof_pref.index(student) < prof_pref.index(current_student):
                        self.profiles_matches[prof].pop()
                        self.profiles_matches[prof].append(student)
                        self.profiles_matches[prof].sort(key=prof_pref.index)
                        self.student_matches[student] = prof
                        self.student_matches[current_student] = None
                        free_students.pop(0)
                        free_students.append(current_student)
            else:
                free_students.pop(0)
        self.unmatched_students = [s for s in range(self.num_students) if self.student_matches[s] is None]
           
    def gale_shapley_short(self, data):
        free_students = [s for s in data if s not in self.reserve_students]
        proposed = {student: 0 for student in range(self.num_students)}
        while free_students:
            student = free_students[0]
            student_pref = self.data_s.loc[student, 'preferences']
            prof_index = proposed[student]
            if prof_index < len(student_pref):  
                prof = student_pref[prof_index]
                proposed[student] += 1
                if len(self.profiles_matches[prof]) < self.data_p['quota'][prof]:
                    self.profiles_matches[prof].append(student)
                    self.student_matches[student] = prof
                    free_students.pop(0)
                    if prof in self.mandatory_profiles and self.reserve_students and len(self.profiles_matches[prof]) < self.data_p['min_quota'][prof]:
                        student_from_reserve = self.reserve_students.pop()
                        free_students.append(student_from_reserve)
            else:
                free_students.pop(0)
        self.unmatched_students = [s for s in range(self.num_students) if self.student_matches[s] is None]
        
    def gale_shapley_redistribution(self):
        free_students = [s for s in self.reserve_students]  
        proposed = {student: 0 for student in range(self.num_students)}
        while free_students:
            student = free_students[0]
            student_pref = self.data_s.loc[student, 'preferences']
            prof_index = proposed[student]
            if prof_index < len(student_pref):  
                prof = student_pref[prof_index]
                proposed[student] += 1
                if self.data_p['quota'][prof] > 0:
                    self.profiles_matches[prof].append(student)
                    self.student_matches[student] = prof
                    free_students.pop(0)
                    self.data_p['quota'][prof] -= 1
                else:
                    current_student = self.profiles_matches[prof][-1]
                    prof_pref = self.data_p['preferences'][prof]
                    if prof_pref.index(student) < prof_pref.index(current_student):
                        self.profiles_matches[prof].pop()
                        self.profiles_matches[prof].append(student)
                        self.profiles_matches[prof].sort(key=prof_pref.index)
                        self.student_matches[student] = prof
                        self.student_matches[current_student] = None
                        free_students.pop(0)
                        free_students.append(current_student)
            else:
                free_students.pop(0)
        self.unmatched_students = [s for s in range(self.num_students) if self.student_matches[s] is None]
        
    def gale_shapley_redistribution_short(self):
        free_students = [s for s in self.reserve_students] 
        sorted_indices = {student: index for index, student in enumerate(self.sorted_students)}
        # Сортируем free_students по индексам из sorted_indices
        free_students.sort(key=lambda student: sorted_indices.get(student, float('inf')))
        proposed = {student: 0 for student in range(self.num_students)}
        while free_students:
            student = free_students[0]
            student_pref = self.data_s.loc[student, 'preferences']
            prof_index = proposed[student]
            if prof_index < len(student_pref): 
                prof = student_pref[prof_index]
                proposed[student] += 1
                if self.data_p['quota'][prof] > 0:
                    self.profiles_matches[prof].append(student)
                    self.student_matches[student] = prof
                    free_students.pop(0)
                    self.data_p['quota'][prof] -= 1
            else:
                free_students.pop(0)
        self.unmatched_students = [s for s in range(self.num_students) if self.student_matches[s] is None]
        
    def calculate_prof_status_and_a(self):
        # Считаем изначально укомплектованные профили и необходимое число студентов
        # статус 0 - некомплектный; 1 - комплектный
        self.prof_status = [0 for item in range(self.data_p.shape[0])]
        sum_to_add = 0
        
        for prof, matched_students in self.profiles_matches.items():
            max_size = self.data_p.loc[prof, 'max_group_size']
            min_size = self.data_p.loc[prof, 'min_group_size']

            full_groups = len(matched_students) // max_size
            small_groups = len(matched_students) // min_size 

            if (small_groups == full_groups) and (len(matched_students) % max_size != 0):
                self.prof_status[prof] = 0
                if prof not in self.mandatory_profiles:
                    students_to_add = min_size - len(matched_students) % min_size
                    sum_to_add += students_to_add
                elif (prof in self.mandatory_profiles) and (len(matched_students) >= self.data_p.loc[prof, 'min_quota']):
                    students_to_add = min_size - len(matched_students) % min_size
                    sum_to_add += students_to_add
            else:
                self.prof_status[prof] = 1
            
            if (prof in self.mandatory_profiles) and (len(matched_students) < self.data_p.loc[prof, 'min_quota']):
                sum_to_add += (self.data_p.loc[prof, 'min_num_groups'] - small_groups - 1) * min_size + (min_size - len(matched_students) % min_size)
        # Обновляем значение a
        self.a = sum_to_add - len(self.reserve_students) - len(self.unmatched_students)
                                                               
    def preparing_for_redistribution(self):
        while True:
            if self.a == 0:
                print('можно проводить распределение')
                print(f'студенты к распределению: {self.reserve_students + self.unmatched_students}')
                break
            
            if self.a < 0:
                print('есть лишние студенты')
                print(f'студенты к распределению: {self.reserve_students + self.unmatched_students}')
                break
                
            # Находим худшего распределённого студента
            result = [item for item in self.sorted_students if item not in self.unmatched_students and item not in self.reserve_students][-1]
            # Убираем его с профиля
            self.profiles_matches[self.student_matches[result]].remove(result)
            # Убираем у него сопоставление с профилем и заносим в список свободных
            current_prof = self.student_matches[result]
            self.student_matches[result] = None
            self.reserve_students.append(result)
            
            # Проверяем комплектность профиля, откуда убрали студента
            matched_students = self.profiles_matches[current_prof]
            max_size = self.data_p.loc[current_prof, 'max_group_size']
            min_size = self.data_p.loc[current_prof, 'min_group_size']
            
            full_groups = len(matched_students) // max_size
            small_groups = len(matched_students) // min_size 
            
            if (small_groups == full_groups) and (len(matched_students) % max_size != 0):
                self.current_prof_status[current_prof] = 0
            else:
                self.current_prof_status[current_prof] = 1

            # Обрабатываем, если профиль обязательный, но студентов на нём достаточно
            if (current_prof in self.mandatory_profiles) and (len(matched_students) >= self.data_p.loc[current_prof, 'min_num_groups'] * min_size):
                if self.current_prof_status[current_prof] == 1:
                    if self.prof_status[current_prof] == 1:
                        self.a -= 1
                    else:                                      
                        self.a -= (small_groups + 1) * min_size - len(matched_students)
            # Обрабатываем, если профиль необязательный
            if current_prof not in self.mandatory_profiles:
                if self.current_prof_status[current_prof] == 1:
                    if self.prof_status[current_prof] == 1:
                        self.a -= 1
                    else:
                        self.a -= (small_groups + 1) * min_size - len(matched_students)                                                   
            # В остальных случаях а не меняется, поэтому ничего не делаем
                                                               

        for prof, matched_students in self.profiles_matches.items():
            max_size = self.data_p.loc[prof, 'max_group_size']
            min_size = self.data_p.loc[prof, 'min_group_size']
            if len(matched_students) > 0:
                full_groups = len(matched_students) // max_size
                small_groups = len(matched_students) // min_size
                if len(matched_students) % max_size == 0:
                    # Обновляем квоту
                    self.data_p.loc[prof, 'quota'] = 0
                elif small_groups == full_groups:
                    students_to_add = min_size - len(matched_students) % min_size
                    # Обновляем квоту
                    self.data_p.loc[prof, 'quota'] = students_to_add
                else:
                    # Обновляем квоту
                    self.data_p.loc[prof, 'quota'] = 0
               #  Обновляем квоту для ненабранных обязательных профилей        
                if (prof in self.mandatory_profiles) and (small_groups < self.data_p.loc[prof, 'min_num_groups']):
                    self.data_p.loc[prof, 'quota'] = self.data_p.loc[prof, 'min_quota'] - matched_students 
       
    def random_distribution(self):
        for student in self.unmatched_students[:]:
            self.unmatched_students.remove(student)
            available_profiles = [prof for prof in range(self.num_profiles) if self.data_p.loc[prof, 'quota'] > 0]
            if available_profiles:  # Если есть доступные профили
                prof = random.choice(available_profiles)  # Случайный профиль
                self.profiles_matches[prof].append(student)  # Записываем студента на профиль
                self.student_matches[student] = prof  # Обновляем сопоставление студента
                self.data_p.loc[prof, 'quota'] -= 1  # Обновляем квоту профиля
            else:
                self.unmatched_students.append(student)

    def thresholds(self, min_threshold, max_threshold):
        i = 0
        while i < len(max_threshold) - 1:
            if min_threshold[i + 1] - 1  <= max_threshold[i]:
                min_threshold.pop(i + 1)
                max_threshold.pop(i)
            else:
                i += 1
        return min_threshold, max_threshold

    def completeness_quota(self):
        for prof, matched_students in self.profiles_matches.items():
    
            min_threshold = []
            max_threshold = []
            available_students = []

            max_size = self.data_p.loc[prof, 'max_group_size']
            min_size = self.data_p.loc[prof, 'min_group_size']
            quota = self.data_p.loc[prof, 'quota']
    
            if max_size // min_size == 0:
                print(f'Профиль {prof} всегда комплектен. Верхняя квота - {quota}')
            else:
                for i in range(1, self.data_p.loc[prof, 'max_num_groups'] + 1):
                    min_threshold.append(min_size * i)
                    max_threshold.append(max_size * i)
            
                min_thresholds, max_thresholds = self.thresholds(min_threshold, max_threshold)
        
                max_available = self.data_p.loc[prof, 'max_group_size'] * self.data_p.loc[prof, 'max_num_groups']
        
                for i in range(len(max_thresholds) - 1):
                    if len(matched_students) <= max_thresholds[i]:
                        if len(matched_students) >= min_thresholds[i+1]:
                            max_available = max_thresholds[i+1]
                            break
                        else:     
                            max_available = max_thresholds[i]
                            break
                print(f'на профиле {prof} студентов можно добавить  до {max_available}')
                self.data_p.loc[prof, 'quota'] = max_available - len(matched_students)
