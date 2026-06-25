import math

GRUPOS_110 = [
    'Enfermedades infecciosas intestinales',
    'Tuberculosis',
    'Ciertas enfermedades transmitidas por vectores y rabia',
    'Ciertas enfermedades inmunoprevenibles',
    'Meningitis',
    'Septicemia, excepto neonatal',
    'Hepatitis B',
    'Enfermedad por el VIH (SIDA)',
    'Otras enfermedades infecciosas y parasitarias',
    'Sífilis congénita',
    'Infecciones especificas del periodo perinatal',
    'Neoplasia maligna de estómago',
    'Neoplasia maligna de colon y de la unión rectosigmoidea',
    'Neoplasia maligna de los órganos digestivos y del peritoneo, excepto estomago',
    'Neoplasia maligna de pancreas',
    'Neoplasia maligna de la tráquea, los bronquios y el pulmón',
    'Neoplasia maligna de los órganos respiratorios e intratorácicos, excepto traquea y pulmon',
    'Neoplasia maligna de la mama',
    'Neoplasia maligna del cuello del útero',
    'Neoplasia maligna del cuerpo del útero',
    'Neoplasia maligna del útero, parte no especificada',
    'Neoplasia maligna de la próstata',
    'Neoplasia maligna de los órganos genitourinarios',
    'Neoplasia maligna de ojo, encefalo y de otras partes del sistema nervioso',
    'Neoplasia maligna de tejido linfático, de otros órganos hematopoyeticos',
    'Leucemia',
    'Neoplasia maligna del labio, de la cavidad bucal y de la faringe',
    'Neoplasia maligna de la piel',
    'Neoplasia maligna de los huesos, cartilagos y tejido conjuntivo',
    'Neoplasia maligna de la glandula tiroides y de otras glandulas endocrinas',
    'Neoplasia maligna de sitios mal definidos, de comportamiento incierto y los no especificados',
    'Neoplasia maligna de higado y vias biliares',
    'Neoplasia maligna secundaria (metastasis)',
    'Neoplasias benignas',
    'Fiebre reumática aguda y enfermedades cardíacas reumáticas cronicas',
    'Enfermedades hipertensivas',
    'Enfermedades isquémicas del corazón',
    'Enfermedad cardiopulmonar, enfermedades de la circulación pulmonar',
    'Enfermedades cerebrovasculares',
    'Arteriosclerosis',
    'Aneurimas',
    'Embolia, trombosis arteriales y otros trastornos arteriales o arteriolares',
    'Insuficiencia cardíaca',
    'Paro cardiaco',
    'Otras enfermedades del sistema circulatorio',
    'Feto y recién nacido afectados por ciertas afecciones materna',
    'Feto y recién nacido afectados por complicaciones obstétrica',
    'Retardo del crecimiento fetal, desnutrición fetal, gestación',
    'Trastornos respiratorios específicos del periodo perinatal',
    'Trastornos cardiovasculares originados en el periodo perinatal',
    'Trastornos hemorragicos y hematologicos del feto y del recien nacido',
    'Trastornos endocrinos y metabolicos del feto y del recien nacido',
    'Trastornos del sistema digestivo del feto y del recien nacido',
    'Otras ciertas afecciones originadas en el periodo perinatal',
    'Infecciones respiratorias agudas altas',
    'Infecciones respiratorias agudas bajas',
    'Enfermedades del pulmon debidas a agentes externos',
    'Enfermedad pulmonar obstructiva cronica (EPOC)',
    'Asma',
    'Edema Pulmonar',
    'Enfermedad pulmonar intersticial',
    'Afecciones de la pleura',
    'Insuficiencia respiratoria',
    'Trastornos respiratorios no especificados',
    'Otras enfermedades del sistema respiratorio',
    'Enfermedades del esofago, estomago y del duodeno',
    'Apendicitis, hernia de la cavidad abdominal y obstrucción intestinal',
    'Enfermedades del peritoneo, peritonitis y otros',
    'Cirrosis y ciertas otras enfermedades crónicas del hígado',
    'Enfermedades del sistema urinario',
    'Hiperplasia de próstata',
    'Trastornos de la vesícula biliar, vias biliares y del pancreas',
    'Hemorragia gastrointestinal (hematemesis, melena y las no especificadas)',
    'Insuficiencia renal, incluye la aguda, cronica y la no especificadas',
    'Otras enfermedades del sistema digestivo',
    'Trastornos mentales y del comportamiento',
    'Enfermedad de Alzheimer',
    'Enfermedad del parkinson',
    'Esclerosis multiple',
    'Epilepsia y estado de mal epileptico',
    'Edema cerebral',
    'Encefalitis viral',
    'Encefalitis, mielitis y encefalomielitis',
    'Otras enfermedades del sistema nervioso, excepto meningitis',
    'Degeneracion de sistemas multiples',
    'Diabetes mellitus',
    'Deficiencias nutricionales y anemias nutricionales',
    'Anemias hemoliticas, aplasticas y otras anemias',
    'Trastornos de la glandula tiroides, endocrinas y otras metabolicas',
    'Defectos de la coagulación en organos hematopoyeticos y trastornos que afectan al mecanismo de la inmunidad',
    'Accidentes de transporte terrestre',
    'Accidentes por otro tipo de transporte',
    'Caídas',
    'Accidentes por fuerzas mecanicas (inanimadas y animadas)',
    'Accidentes por Ahogamiento y sumersión',
    'Accidentes que obstruyen la respiración',
    'Exposición a la corriente eléctrica',
    'Exposición al humo, fuego y llamas',
    'Accidentes por fuerzas de la naturaleza',
    'Envenenamientos por, y exposición a sustancias nocivas',
    'Accidentes por disparo de arma de fuego',
    'Incidentes ocurridos al paciente durante la atencion medica y quirurgica',
    'Suicidios (lesiones autoinfligidas intencionalmente)',
    'Homicidios (agresiones infligidas por otra persona)',
    'Lesiones de intención no determinada',
    'Las demás causas externas',
    'Covid-19',
    'Eventos relacionados al embarazo, parto y puerperio',
    'Malformaciones congénitas, deformidades y anomalías cromosomicas',
    'Enfermedades de la piel',
    'Resto de las demas enfermedades',
]


def _expand_range(start, end):
    """Generate all ICD-10 3-char codes from start to end inclusive."""
    result = []
    sl = start[0]
    sn = int(start[1:])
    el = end[0]
    en = int(end[1:])
    cur_l = sl
    cur_n = sn
    while True:
        if cur_n > 99:
            cur_l = chr(ord(cur_l) + 1)
            cur_n = 0
            continue
        result.append(f"{cur_l}{cur_n:02d}")
        if cur_l == el and cur_n == en:
            break
        cur_n += 1
    return result


def build_mapping():
    """Return a dict mapping ICD-10 3-char prefix to grupo110 name."""
    mapping = {}

    range_defs = [
        # ===== Chapter I: Infectious and parasitic diseases (A00-B99) =====
        ('A00', 'A09', 'Enfermedades infecciosas intestinales'),
        ('A10', 'A14', 'Otras enfermedades infecciosas y parasitarias'),
        ('A15', 'A19', 'Tuberculosis'),
        ('A20', 'A32', 'Otras enfermedades infecciosas y parasitarias'),
        ('A33', 'A37', 'Ciertas enfermedades inmunoprevenibles'),
        ('A38', 'A38', 'Otras enfermedades infecciosas y parasitarias'),
        ('A39', 'A39', 'Meningitis'),
        ('A40', 'A41', 'Septicemia, excepto neonatal'),
        ('A42', 'A49', 'Otras enfermedades infecciosas y parasitarias'),
        ('A50', 'A50', 'Sífilis congénita'),
        ('A51', 'A79', 'Otras enfermedades infecciosas y parasitarias'),
        ('A80', 'A80', 'Ciertas enfermedades inmunoprevenibles'),
        ('A81', 'A81', 'Otras enfermedades infecciosas y parasitarias'),
        ('A82', 'A84', 'Ciertas enfermedades transmitidas por vectores y rabia'),
        ('A85', 'A86', 'Encefalitis viral'),
        ('A87', 'A87', 'Meningitis'),
        ('A88', 'A89', 'Otras enfermedades infecciosas y parasitarias'),
        ('A90', 'A99', 'Ciertas enfermedades transmitidas por vectores y rabia'),
        ('B00', 'B00', 'Otras enfermedades infecciosas y parasitarias'),
        ('B01', 'B01', 'Ciertas enfermedades inmunoprevenibles'),
        ('B02', 'B02', 'Otras enfermedades infecciosas y parasitarias'),
        ('B03', 'B03', 'Ciertas enfermedades inmunoprevenibles'),
        ('B04', 'B04', 'Otras enfermedades infecciosas y parasitarias'),
        ('B05', 'B06', 'Ciertas enfermedades inmunoprevenibles'),
        ('B07', 'B14', 'Otras enfermedades infecciosas y parasitarias'),
        ('B15', 'B19', 'Hepatitis B'),
        ('B20', 'B24', 'Enfermedad por el VIH (SIDA)'),
        ('B25', 'B25', 'Otras enfermedades infecciosas y parasitarias'),
        ('B26', 'B26', 'Ciertas enfermedades inmunoprevenibles'),
        ('B27', 'B49', 'Otras enfermedades infecciosas y parasitarias'),
        ('B50', 'B57', 'Ciertas enfermedades transmitidas por vectores y rabia'),
        ('B58', 'B99', 'Otras enfermedades infecciosas y parasitarias'),

        # ===== Chapter II: Neoplasms (C00-D48) =====
        ('C00', 'C14', 'Neoplasia maligna del labio, de la cavidad bucal y de la faringe'),
        ('C15', 'C15', 'Neoplasia maligna de los órganos digestivos y del peritoneo, excepto estomago'),
        ('C16', 'C16', 'Neoplasia maligna de estómago'),
        ('C17', 'C17', 'Neoplasia maligna de los órganos digestivos y del peritoneo, excepto estomago'),
        ('C18', 'C21', 'Neoplasia maligna de colon y de la unión rectosigmoidea'),
        ('C22', 'C24', 'Neoplasia maligna de higado y vias biliares'),
        ('C25', 'C25', 'Neoplasia maligna de pancreas'),
        ('C26', 'C26', 'Neoplasia maligna de los órganos digestivos y del peritoneo, excepto estomago'),
        ('C30', 'C32', 'Neoplasia maligna de los órganos respiratorios e intratorácicos, excepto traquea y pulmon'),
        ('C33', 'C34', 'Neoplasia maligna de la tráquea, los bronquios y el pulmón'),
        ('C37', 'C39', 'Neoplasia maligna de los órganos respiratorios e intratorácicos, excepto traquea y pulmon'),
        ('C40', 'C41', 'Neoplasia maligna de los huesos, cartilagos y tejido conjuntivo'),
        ('C43', 'C44', 'Neoplasia maligna de la piel'),
        ('C45', 'C45', 'Neoplasia maligna de los órganos respiratorios e intratorácicos, excepto traquea y pulmon'),
        ('C46', 'C46', 'Neoplasia maligna de tejido linfático, de otros órganos hematopoyeticos'),
        ('C47', 'C47', 'Neoplasia maligna de los huesos, cartilagos y tejido conjuntivo'),
        ('C48', 'C48', 'Neoplasia maligna de los órganos digestivos y del peritoneo, excepto estomago'),
        ('C49', 'C49', 'Neoplasia maligna de los huesos, cartilagos y tejido conjuntivo'),
        ('C50', 'C50', 'Neoplasia maligna de la mama'),
        ('C51', 'C52', 'Neoplasia maligna de los órganos genitourinarios'),
        ('C53', 'C53', 'Neoplasia maligna del cuello del útero'),
        ('C54', 'C54', 'Neoplasia maligna del cuerpo del útero'),
        ('C55', 'C55', 'Neoplasia maligna del útero, parte no especificada'),
        ('C56', 'C58', 'Neoplasia maligna de los órganos genitourinarios'),
        ('C60', 'C60', 'Neoplasia maligna de los órganos genitourinarios'),
        ('C61', 'C61', 'Neoplasia maligna de la próstata'),
        ('C62', 'C68', 'Neoplasia maligna de los órganos genitourinarios'),
        ('C69', 'C72', 'Neoplasia maligna de ojo, encefalo y de otras partes del sistema nervioso'),
        ('C73', 'C75', 'Neoplasia maligna de la glandula tiroides y de otras glandulas endocrinas'),
        ('C76', 'C76', 'Neoplasia maligna de sitios mal definidos, de comportamiento incierto y los no especificados'),
        ('C77', 'C79', 'Neoplasia maligna secundaria (metastasis)'),
        ('C80', 'C80', 'Neoplasia maligna de sitios mal definidos, de comportamiento incierto y los no especificados'),
        ('C81', 'C86', 'Neoplasia maligna de tejido linfático, de otros órganos hematopoyeticos'),
        ('C88', 'C88', 'Neoplasia maligna de tejido linfático, de otros órganos hematopoyeticos'),
        ('C90', 'C90', 'Neoplasia maligna de tejido linfático, de otros órganos hematopoyeticos'),
        ('C91', 'C95', 'Leucemia'),
        ('C96', 'C96', 'Neoplasia maligna de tejido linfático, de otros órganos hematopoyeticos'),
        ('C97', 'C97', 'Neoplasia maligna de sitios mal definidos, de comportamiento incierto y los no especificados'),
        ('D00', 'D09', 'Neoplasia maligna de sitios mal definidos, de comportamiento incierto y los no especificados'),
        ('D10', 'D36', 'Neoplasias benignas'),
        ('D37', 'D48', 'Neoplasia maligna de sitios mal definidos, de comportamiento incierto y los no especificados'),

        # ===== Chapter III: Blood and immune disorders (D50-D89) =====
        ('D50', 'D64', 'Anemias hemoliticas, aplasticas y otras anemias'),
        ('D65', 'D84', 'Defectos de la coagulación en organos hematopoyeticos y trastornos que afectan al mecanismo de la inmunidad'),
        ('D86', 'D86', 'Defectos de la coagulación en organos hematopoyeticos y trastornos que afectan al mecanismo de la inmunidad'),
        ('D89', 'D89', 'Defectos de la coagulación en organos hematopoyeticos y trastornos que afectan al mecanismo de la inmunidad'),

        # ===== Chapter IV: Endocrine, nutritional and metabolic (E00-E90) =====
        ('E00', 'E07', 'Trastornos de la glandula tiroides, endocrinas y otras metabolicas'),
        ('E10', 'E14', 'Diabetes mellitus'),
        ('E15', 'E35', 'Trastornos de la glandula tiroides, endocrinas y otras metabolicas'),
        ('E40', 'E64', 'Deficiencias nutricionales y anemias nutricionales'),
        ('E65', 'E90', 'Trastornos de la glandula tiroides, endocrinas y otras metabolicas'),

        # ===== Chapter V: Mental and behavioural disorders (F00-F99) =====
        ('F00', 'F99', 'Trastornos mentales y del comportamiento'),

        # ===== Chapter VI: Nervous system (G00-G99) =====
        ('G00', 'G03', 'Meningitis'),
        ('G04', 'G05', 'Encefalitis, mielitis y encefalomielitis'),
        ('G06', 'G09', 'Otras enfermedades del sistema nervioso, excepto meningitis'),
        ('G10', 'G14', 'Degeneracion de sistemas multiples'),
        ('G20', 'G21', 'Enfermedad del parkinson'),
        ('G22', 'G22', 'Enfermedad del parkinson'),
        ('G23', 'G23', 'Degeneracion de sistemas multiples'),
        ('G24', 'G26', 'Otras enfermedades del sistema nervioso, excepto meningitis'),
        ('G30', 'G30', 'Enfermedad de Alzheimer'),
        ('G31', 'G32', 'Degeneracion de sistemas multiples'),
        ('G35', 'G37', 'Esclerosis multiple'),
        ('G40', 'G41', 'Epilepsia y estado de mal epileptico'),
        ('G43', 'G44', 'Otras enfermedades del sistema nervioso, excepto meningitis'),
        ('G45', 'G46', 'Enfermedades cerebrovasculares'),
        ('G47', 'G64', 'Otras enfermedades del sistema nervioso, excepto meningitis'),
        ('G70', 'G90', 'Otras enfermedades del sistema nervioso, excepto meningitis'),
        ('G91', 'G91', 'Edema cerebral'),
        ('G92', 'G92', 'Otras enfermedades del sistema nervioso, excepto meningitis'),
        ('G93', 'G93', 'Edema cerebral'),
        ('G94', 'G99', 'Otras enfermedades del sistema nervioso, excepto meningitis'),

        # ===== Chapter VII/VIII: Eye/Ear (H00-H95) -> fallback Resto =====

        # ===== Chapter IX: Circulatory system (I00-I99) =====
        ('I00', 'I09', 'Fiebre reumática aguda y enfermedades cardíacas reumáticas cronicas'),
        ('I10', 'I15', 'Enfermedades hipertensivas'),
        ('I20', 'I25', 'Enfermedades isquémicas del corazón'),
        ('I26', 'I28', 'Enfermedad cardiopulmonar, enfermedades de la circulación pulmonar'),
        ('I30', 'I45', 'Otras enfermedades del sistema circulatorio'),
        ('I46', 'I46', 'Paro cardiaco'),
        ('I47', 'I49', 'Otras enfermedades del sistema circulatorio'),
        ('I50', 'I50', 'Insuficiencia cardíaca'),
        ('I51', 'I52', 'Otras enfermedades del sistema circulatorio'),
        ('I60', 'I69', 'Enfermedades cerebrovasculares'),
        ('I70', 'I70', 'Arteriosclerosis'),
        ('I71', 'I72', 'Aneurimas'),
        ('I73', 'I77', 'Embolia, trombosis arteriales y otros trastornos arteriales o arteriolares'),
        ('I78', 'I79', 'Otras enfermedades del sistema circulatorio'),
        ('I80', 'I82', 'Embolia, trombosis arteriales y otros trastornos arteriales o arteriolares'),
        ('I83', 'I99', 'Otras enfermedades del sistema circulatorio'),

        # ===== Chapter X: Respiratory system (J00-J99) =====
        ('J00', 'J06', 'Infecciones respiratorias agudas altas'),
        ('J09', 'J22', 'Infecciones respiratorias agudas bajas'),
        ('J30', 'J34', 'Otras enfermedades del sistema respiratorio'),
        ('J35', 'J36', 'Infecciones respiratorias agudas altas'),
        ('J37', 'J39', 'Otras enfermedades del sistema respiratorio'),
        ('J40', 'J44', 'Enfermedad pulmonar obstructiva cronica (EPOC)'),
        ('J45', 'J46', 'Asma'),
        ('J47', 'J47', 'Otras enfermedades del sistema respiratorio'),
        ('J60', 'J70', 'Enfermedades del pulmon debidas a agentes externos'),
        ('J80', 'J81', 'Edema Pulmonar'),
        ('J82', 'J82', 'Otras enfermedades del sistema respiratorio'),
        ('J84', 'J84', 'Enfermedad pulmonar intersticial'),
        ('J85', 'J86', 'Afecciones de la pleura'),
        ('J90', 'J94', 'Afecciones de la pleura'),
        ('J95', 'J95', 'Trastornos respiratorios no especificados'),
        ('J96', 'J96', 'Insuficiencia respiratoria'),
        ('J97', 'J98', 'Trastornos respiratorios no especificados'),
        ('J99', 'J99', 'Otras enfermedades del sistema respiratorio'),

        # ===== Chapter XI: Digestive system (K00-K93) =====
        ('K00', 'K14', 'Enfermedades del esofago, estomago y del duodeno'),
        ('K20', 'K31', 'Enfermedades del esofago, estomago y del duodeno'),
        ('K35', 'K46', 'Apendicitis, hernia de la cavidad abdominal y obstrucción intestinal'),
        ('K50', 'K55', 'Enfermedades del peritoneo, peritonitis y otros'),
        ('K56', 'K56', 'Apendicitis, hernia de la cavidad abdominal y obstrucción intestinal'),
        ('K57', 'K69', 'Enfermedades del peritoneo, peritonitis y otros'),
        ('K70', 'K77', 'Cirrosis y ciertas otras enfermedades crónicas del hígado'),
        ('K80', 'K87', 'Trastornos de la vesícula biliar, vias biliares y del pancreas'),
        ('K90', 'K91', 'Otras enfermedades del sistema digestivo'),
        ('K92', 'K92', 'Hemorragia gastrointestinal (hematemesis, melena y las no especificadas)'),
        ('K93', 'K93', 'Otras enfermedades del sistema digestivo'),

        # ===== Chapter XII: Skin (L00-L99) =====
        ('L00', 'L99', 'Enfermedades de la piel'),

        # ===== Chapter XIII: Musculoskeletal (M00-M99) -> fallback Resto =====

        # ===== Chapter XIV: Genitourinary (N00-N99) =====
        ('N00', 'N16', 'Enfermedades del sistema urinario'),
        ('N17', 'N19', 'Insuficiencia renal, incluye la aguda, cronica y la no especificadas'),
        ('N20', 'N23', 'Enfermedades del sistema urinario'),
        ('N25', 'N39', 'Enfermedades del sistema urinario'),
        ('N40', 'N40', 'Hiperplasia de próstata'),
        ('N41', 'N41', 'Resto de las demas enfermedades'),
        ('N42', 'N42', 'Hiperplasia de próstata'),
        ('N43', 'N99', 'Resto de las demas enfermedades'),

        # ===== Chapter XV: Pregnancy, childbirth (O00-O99) =====
        ('O00', 'O99', 'Eventos relacionados al embarazo, parto y puerperio'),

        # ===== Chapter XVI: Perinatal conditions (P00-P96) =====
        ('P00', 'P00', 'Feto y recién nacido afectados por ciertas afecciones materna'),
        ('P04', 'P04', 'Feto y recién nacido afectados por ciertas afecciones materna'),
        ('P01', 'P03', 'Feto y recién nacido afectados por complicaciones obstétrica'),
        ('P10', 'P15', 'Feto y recién nacido afectados por complicaciones obstétrica'),
        ('P05', 'P05', 'Retardo del crecimiento fetal, desnutrición fetal, gestación'),
        ('P07', 'P08', 'Retardo del crecimiento fetal, desnutrición fetal, gestación'),
        ('P20', 'P22', 'Trastornos respiratorios específicos del periodo perinatal'),
        ('P23', 'P23', 'Infecciones especificas del periodo perinatal'),
        ('P24', 'P28', 'Trastornos respiratorios específicos del periodo perinatal'),
        ('P29', 'P29', 'Trastornos cardiovasculares originados en el periodo perinatal'),
        ('P35', 'P39', 'Infecciones especificas del periodo perinatal'),
        ('P50', 'P54', 'Trastornos hemorragicos y hematologicos del feto y del recien nacido'),
        ('P55', 'P59', 'Trastornos endocrinos y metabolicos del feto y del recien nacido'),
        ('P60', 'P61', 'Trastornos hemorragicos y hematologicos del feto y del recien nacido'),
        ('P70', 'P74', 'Trastornos endocrinos y metabolicos del feto y del recien nacido'),
        ('P75', 'P78', 'Trastornos del sistema digestivo del feto y del recien nacido'),
        ('P80', 'P81', 'Otras ciertas afecciones originadas en el periodo perinatal'),
        ('P83', 'P91', 'Otras ciertas afecciones originadas en el periodo perinatal'),
        ('P92', 'P92', 'Trastornos del sistema digestivo del feto y del recien nacido'),
        ('P93', 'P96', 'Otras ciertas afecciones originadas en el periodo perinatal'),

        # ===== Chapter XVII: Congenital malformations (Q00-Q99) =====
        ('Q00', 'Q99', 'Malformaciones congénitas, deformidades y anomalías cromosomicas'),

        # ===== Chapter XVIII: Symptoms, signs (R00-R99) =====
        ('R00', 'R99', 'Resto de las demas enfermedades'),

        # ===== Chapter XIX: Injury, poisoning (S00-T98) -> fallback Resto =====

        # ===== Chapter XX: External causes of morbidity and mortality (V01-Y98) =====
        ('V01', 'V79', 'Accidentes de transporte terrestre'),
        ('V80', 'V82', 'Accidentes por otro tipo de transporte'),
        ('V83', 'V89', 'Accidentes de transporte terrestre'),
        ('V90', 'V99', 'Accidentes por otro tipo de transporte'),
        ('W00', 'W19', 'Caídas'),
        ('W20', 'W31', 'Accidentes por fuerzas mecanicas (inanimadas y animadas)'),
        ('W32', 'W34', 'Accidentes por disparo de arma de fuego'),
        ('W35', 'W64', 'Accidentes por fuerzas mecanicas (inanimadas y animadas)'),
        ('W65', 'W74', 'Accidentes por Ahogamiento y sumersión'),
        ('W75', 'W84', 'Accidentes que obstruyen la respiración'),
        ('W85', 'W87', 'Exposición a la corriente eléctrica'),
        ('W88', 'W99', 'Las demás causas externas'),
        ('X00', 'X09', 'Exposición al humo, fuego y llamas'),
        ('X10', 'X29', 'Las demás causas externas'),
        ('X30', 'X39', 'Accidentes por fuerzas de la naturaleza'),
        ('X40', 'X49', 'Envenenamientos por, y exposición a sustancias nocivas'),
        ('X50', 'X59', 'Las demás causas externas'),
        ('X60', 'X84', 'Suicidios (lesiones autoinfligidas intencionalmente)'),
        ('X85', 'Y09', 'Homicidios (agresiones infligidas por otra persona)'),
        ('Y10', 'Y34', 'Lesiones de intención no determinada'),
        ('Y35', 'Y36', 'Las demás causas externas'),
        ('Y40', 'Y84', 'Incidentes ocurridos al paciente durante la atencion medica y quirurgica'),
        ('Y85', 'Y98', 'Las demás causas externas'),

        # ===== Chapter XXI: Health status (Z00-Z99) -> fallback Resto =====

        # ===== Chapter XXII: Codes for special purposes (U00-U99) =====
        ('U07', 'U07', 'Covid-19'),
    ]

    for start, end, group in range_defs:
        for code in _expand_range(start, end):
            mapping[code] = group

    return mapping


_MAPPING = build_mapping()


def map_ciex_to_grupo110(ciex_code):
    """
    Map an ICD-10 code (CIE-10) to the corresponding 110-group name.

    Parameters
    ----------
    ciex_code : str or float or None
        The ICD-10 code, e.g. 'I714', 'J960', 'SIN REGISTRO'.

    Returns
    -------
    str
        The name of the 110-cause-of-death group.
    """
    if ciex_code is None:
        return 'Resto de las demas enfermedades'

    if isinstance(ciex_code, float) and math.isnan(ciex_code):
        return 'Resto de las demas enfermedades'

    code_str = str(ciex_code).strip()
    if code_str.upper() == 'SIN REGISTRO':
        return 'Resto de las demas enfermedades'

    prefix = code_str[:3].upper()
    return _MAPPING.get(prefix, 'Resto de las demas enfermedades')
