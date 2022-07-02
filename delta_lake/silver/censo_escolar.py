# Databricks notebook source
# Pyspark
import pyspark.sql.functions as f
from pyspark.sql.window import Window
from pyspark.sql.types import IntegerType, StringType

# COMMAND ----------

# MAGIC %run ../lib/delta_lake

# COMMAND ----------

# Set parameters
dbutils.widgets.text("year","")

# Get parameters
year = dbutils.widgets.get("year")

# Filepath
filepath_censo_escolar = ""

# Get file to process
files_censo_escolar = get_files(".*{}.*".format(year),filepath_censo_escolar)
files_censo_escolar = files_censo_escolar[0]
print("Processing file: {}".format(files_censo_escolar))

# COMMAND ----------

# Read files
df_censo_escolar = spark.read.format("csv").option("sep",";").option("encoding","latin1").option("header","True").load(files_censo_escolar)

# Repartition
df_censo_escolar = df_censo_escolar.repartition(sc.defaultParallelism)

# COMMAND ----------

# Change Data Types
select_datatypes = []
for column in df_censo_escolar.columns:
  if(column.startswith("QT_")):
    tmp = f.col(column).cast(IntegerType()).alias(column)
  elif(column.startswith("DT_")):
    tmp = f.to_date(f.substring(f.col(column),1,9),format="ddMMMyyyy").alias(column)
  else:
    tmp = f.col(column).cast(StringType()).alias(column)
  select_datatypes.append(tmp)

# Convert columns to correct schema
df_censo_escolar = df_censo_escolar.select(*select_datatypes)

# COMMAND ----------

# Columns to get max values
max_columns = ["QT_EQUIP_DVD","QT_EQUIP_SOM","QT_EQUIP_TV","QT_EQUIP_LOUSA_DIGITAL","QT_EQUIP_MULTIMIDIA","QT_DESKTOP_ALUNO","QT_COMP_PORTATIL_ALUNO","QT_TABLET_ALUNO","QT_PROF_ADMINISTRATIVOS","QT_PROF_SERVICOS_GERAIS","QT_PROF_BIBLIOTECARIO","QT_PROF_SAUDE","QT_PROF_COORDENADOR","QT_PROF_FONAUDIOLOGO","QT_PROF_NUTRICIONISTA","QT_PROF_PSICOLOGO","QT_PROF_ALIMENTACAO","QT_PROF_PEDAGOGIA","QT_PROF_SECRETARIO","QT_PROF_SEGURANCA","QT_PROF_MONITORES","QT_PROF_GESTAO"]

# Create select to get max values + 1 (filter values 88888 before get max)
select_max_column = []
for column in max_columns:
  select_max_column.append(f.expr("max({0} + 1) filter (where {0} != '88888') as {0}".format(column)))

# Get max vallues
max_values = df_censo_escolar.select(*select_max_column).collect()[0]
max_values = max_values.asDict()

# Create select to set this max values when 88888 appear in column
select_case_when_max = []
for column in max_values:
  select_case_when_max.append(f.expr("CASE WHEN {0} == 88888 THEN {1} ELSE {0} END AS {0}".format(column,max_values[column])))

# COMMAND ----------

# Create select for cnpj columns
cnpj_columns = ["NU_CNPJ_ESCOLA_PRIVADA","NU_CNPJ_MANTENEDORA"]
select_cnpj_columns = []
for column in cnpj_columns:
  select_cnpj_columns.append(f.expr("CASE WHEN {0} == '99999999999999' THEN NULL ELSE {0} END AS {0}".format(column)))

# COMMAND ----------

# Create select for "ocupacao" columns
ocupacao_columns = ["TP_OCUPACAO_PREDIO_ESCOLAR","TP_OCUPACAO_GALPAO"]
ocupacao_dict = {"1":"Próprio","2":"Alugado","3":"Cedido"}
select_ocupacao = []
for column in ocupacao_columns:
   select_ocupacao.append(build_case_when(ocupacao_dict,column,"==",column))

# Create select for "atividade" columns
atividade_columns = ["TP_AEE","TP_ATIVIDADE_COMPLEMENTAR"]
atividade_dict = {"0":"Nao oferece","1":"Nao exclusivamente","2":"Exclusivamente"}
select_atividade = []
for column in atividade_columns:
   select_atividade.append(build_case_when(atividade_dict,column,"==",column))

# Create select for "nao sim" columns
nao_sim_columns = ["IN_LOCAL_FUNC_PREDIO_ESCOLAR","IN_LOCAL_FUNC_SALAS_EMPRESA","IN_LOCAL_FUNC_SOCIOEDUCATIVO","IN_LOCAL_FUNC_UNID_PRISIONAL","IN_LOCAL_FUNC_PRISIONAL_SOCIO","IN_LOCAL_FUNC_TEMPLO_IGREJA","IN_LOCAL_FUNC_CASA_PROFESSOR","IN_LOCAL_FUNC_GALPAO","IN_LOCAL_FUNC_SALAS_OUTRA_ESC","IN_LOCAL_FUNC_OUTROS","IN_AGUA_FILTRADA","IN_AGUA_POTAVEL","IN_AGUA_REDE_PUBLICA","IN_AGUA_POCO_ARTESIANO","IN_AGUA_CACIMBA","IN_AGUA_FONTE_RIO","IN_AGUA_INEXISTENTE","IN_ENERGIA_REDE_PUBLICA","IN_ENERGIA_GERADOR","IN_ENERGIA_GERADOR_FOSSIL","IN_ENERGIA_OUTROS","IN_ENERGIA_RENOVAVEL","IN_ENERGIA_INEXISTENTE","IN_ESGOTO_REDE_PUBLICA","IN_ESGOTO_FOSSA_SEPTICA","IN_ESGOTO_FOSSA_COMUM","IN_ESGOTO_FOSSA","IN_ESGOTO_INEXISTENTE","IN_LIXO_SERVICO_COLETA","IN_LIXO_QUEIMA","IN_LIXO_ENTERRA","IN_LIXO_DESTINO_FINAL_PUBLICO","IN_LIXO_DESCARTA_OUTRA_AREA","IN_LIXO_JOGA_OUTRA_AREA","IN_LIXO_OUTROS","IN_LIXO_RECICLA","IN_ALMOXARIFADO","IN_AREA_VERDE","IN_AUDITORIO","IN_BANHEIRO_FORA_PREDIO","IN_BANHEIRO_DENTRO_PREDIO","IN_BANHEIRO","IN_BANHEIRO_EI","IN_BANHEIRO_PNE","IN_BANHEIRO_FUNCIONARIOS","IN_BANHEIRO_CHUVEIRO","IN_BERCARIO","IN_BIBLIOTECA","IN_BIBLIOTECA_SALA_LEITURA","IN_COZINHA","IN_DESPENSA","IN_DORMITORIO_ALUNO","IN_DORMITORIO_PROFESSOR","IN_LABORATORIO_CIENCIAS","IN_LABORATORIO_INFORMATICA","IN_PATIO_COBERTO","IN_PATIO_DESCOBERTO","IN_PARQUE_INFANTIL","IN_PISCINA","IN_QUADRA_ESPORTES","IN_QUADRA_ESPORTES_COBERTA","IN_QUADRA_ESPORTES_DESCOBERTA","IN_REFEITORIO","IN_SALA_ATELIE_ARTES","IN_SALA_MUSICA_CORAL","IN_SALA_ESTUDIO_DANCA","IN_SALA_MULTIUSO","IN_SALA_DIRETORIA","IN_SALA_LEITURA","IN_SALA_PROFESSOR","IN_SALA_REPOUSO_ALUNO","IN_SECRETARIA","IN_SALA_ATENDIMENTO_ESPECIAL","IN_TERREIRAO","IN_VIVEIRO","IN_DEPENDENCIAS_PNE","IN_LAVANDERIA","IN_DEPENDENCIAS_OUTRAS","IN_ACESSIBILIDADE_CORRIMAO","IN_ACESSIBILIDADE_ELEVADOR","IN_ACESSIBILIDADE_PISOS_TATEIS","IN_ACESSIBILIDADE_VAO_LIVRE","IN_ACESSIBILIDADE_RAMPAS","IN_ACESSIBILIDADE_SINAL_SONORO","IN_ACESSIBILIDADE_SINAL_TATIL","IN_ACESSIBILIDADE_SINAL_VISUAL","IN_ACESSIBILIDADE_INEXISTENTE","IN_EQUIP_PARABOLICA","IN_COMPUTADOR","IN_EQUIP_COPIADORA","IN_EQUIP_IMPRESSORA","IN_EQUIP_IMPRESSORA_MULT","IN_EQUIP_SCANNER","IN_EQUIP_NENHUM","IN_EQUIP_DVD","IN_EQUIP_SOM","IN_EQUIP_TV","IN_EQUIP_LOUSA_DIGITAL","IN_EQUIP_MULTIMIDIA","IN_EQUIP_VIDEOCASSETE","IN_EQUIP_RETROPROJETOR","IN_EQUIP_FAX","IN_EQUIP_FOTO","IN_DESKTOP_ALUNO","IN_COMP_PORTATIL_ALUNO","IN_TABLET_ALUNO","IN_INTERNET","IN_INTERNET_ALUNOS","IN_INTERNET_ADMINISTRATIVO","IN_INTERNET_APRENDIZAGEM","IN_INTERNET_COMUNIDADE","IN_PROF_ADMINISTRATIVOS","IN_PROF_SERVICOS_GERAIS","IN_PROF_BIBLIOTECARIO","IN_PROF_SAUDE","IN_PROF_COORDENADOR","IN_PROF_FONAUDIOLOGO","IN_PROF_NUTRICIONISTA","IN_PROF_PSICOLOGO","IN_PROF_ALIMENTACAO","IN_PROF_PEDAGOGIA","IN_PROF_SECRETARIO","IN_PROF_SEGURANCA","IN_PROF_MONITORES","IN_PROF_GESTAO","IN_PROF_ASSIST_SOCIAL","IN_MATERIAL_PED_MULTIMIDIA","IN_MATERIAL_PED_INFANTIL","IN_MATERIAL_PED_CIENTIFICO","IN_MATERIAL_PED_DIFUSAO","IN_MATERIAL_PED_MUSICAL","IN_MATERIAL_PED_JOGOS","IN_MATERIAL_PED_ARTISTICAS","IN_MATERIAL_PED_DESPORTIVA","IN_MATERIAL_PED_INDIGENA","IN_MATERIAL_PED_ETNICO","IN_MATERIAL_PED_CAMPO","IN_MATERIAL_PED_NENHUM","IN_MATERIAL_ESP_QUILOMBOLA","IN_MATERIAL_ESP_INDIGENA","IN_MATERIAL_ESP_NAO_UTILIZA","IN_EDUCACAO_INDIGENA","IN_BRASIL_ALFABETIZADO","IN_FINAL_SEMANA","IN_ORGAO_ASS_PAIS","IN_ORGAO_ASS_PAIS_MESTRES","IN_ORGAO_CONSELHO_ESCOLAR","IN_ORGAO_GREMIO_ESTUDANTIL","IN_ORGAO_OUTROS","IN_ORGAO_NENHUM","IN_MEDIACAO_PRESENCIAL","IN_MEDIACAO_SEMIPRESENCIAL","IN_MEDIACAO_EAD","IN_REGULAR","IN_DIURNO","IN_NOTURNO","IN_EAD","IN_BAS","IN_INF","IN_INF_CRE","IN_INF_PRE","IN_FUND","IN_FUND_AI","IN_FUND_AF","IN_MED","IN_PROF","IN_PROF_TEC","IN_EJA","IN_EJA_FUND","IN_EJA_MED","IN_ESP","IN_ESP_CC","IN_ESP_CE","IN_VINCULO_SECRETARIA_EDUCACAO","IN_VINCULO_SEGURANCA_PUBLICA","IN_VINCULO_SECRETARIA_SAUDE","IN_VINCULO_OUTRO_ORGAO","IN_CONVENIADA_PP","IN_MANT_ESCOLA_PRIVADA_EMP","IN_MANT_ESCOLA_PRIVADA_ONG","IN_MANT_ESCOLA_PRIVADA_OSCIP","IN_MANT_ESCOLA_PRIV_ONG_OSCIP","IN_MANT_ESCOLA_PRIVADA_SIND","IN_MANT_ESCOLA_PRIVADA_SIST_S","IN_MANT_ESCOLA_PRIVADA_S_FINS","IN_PREDIO_COMPARTILHADO","IN_BANDA_LARGA","IN_RESERVA_PPI","IN_RESERVA_RENDA","IN_RESERVA_PUBLICA","IN_RESERVA_PCD","IN_RESERVA_OUTROS","IN_RESERVA_NENHUMA","IN_TRATAMENTO_LIXO_SEPARACAO","IN_TRATAMENTO_LIXO_REUTILIZA","IN_TRATAMENTO_LIXO_RECICLAGEM","IN_TRATAMENTO_LIXO_INEXISTENTE","IN_ACESSO_INTERNET_COMPUTADOR","IN_ACES_INTERNET_DISP_PESSOAIS","IN_SERIE_ANO","IN_PERIODOS_SEMESTRAIS","IN_FUNDAMENTAL_CICLOS","IN_GRUPOS_NAO_SERIADOS","IN_MODULOS","IN_FORMACAO_ALTERNANCIA","IN_EXAME_SELECAO","IN_REDES_SOCIAIS","IN_ESPACO_ATIVIDADE","IN_ESPACO_EQUIPAMENTO"]
nao_sim_dict = {"0":"Não","B":"Sim"}
select_nao_sim = []
for column in nao_sim_columns:
   select_nao_sim.append(build_case_when(nao_sim_dict,column,"==",column))

# COMMAND ----------

# Columns with "de para"
depara_columns = [("TP_DEPENDENCIA",{"1":"Federal","2":"Estadual","3":"Municipal","4":"Privada"}),("TP_CATEGORIA_ESCOLA_PRIVADA",{"1":"Particular","2":"Comunitária","3":"Confessional","4":"Filantrópica"}),("TP_LOCALIZACAO",{"1":"Urbana","2":"Rural"}),("TP_LOCALIZACAO_DIFERENCIADA",{"0":"A escola não está em área de localização diferenciada","1":"Área de assentamento","2":"Terra indígena","3":"Área onde se localiza comunidade remanescente de quilombos"}),("TP_SITUACAO_FUNCIONAMENTO",{"1":"Em Atividade","2":"Paralisada","3":"Extinta (ano do Censo)","4":"Extinta em Anos Anteriores"}),("TP_CONVENIO_PODER_PUBLICO",{"1":"Municipal","2":"Estadual","3":"Estadual e Municipal"}),("TP_REGULAMENTACAO",{"0":"Não","1":"Sim","2":"Em tramitação"}),("TP_RESPONSAVEL_REGULAMENTACAO",{"1":"Federal","2":"Estadual","3":"Municipal","4":"Estadual e Municipal","5":"Federal e Estadual","6":"Federal, Estadual e Municipal"}),("TP_REDE_LOCAL",{"0":"Não há rede local interligando computadores","1":"A cabo","2":"Wireless","3":"A cabo e Wireless"}),("IN_ALIMENTACAO",{"0":"Não oferece","1":"Oferece"}),("TP_INDIGENA_LINGUA",{"1":"Somente em Língua Indígena","2":"Somente em Língua Portuguesa","3":"Em Língua Indígena e em Língua Portuguesa"}),("TP_PROPOSTA_PEDAGOGICA",{"0":"Não","1":"Sim","2":"A escola não possui projeto político pedagógico/proposta pedagógica"})]

# Create select de para
select_depara = []
for column in depara_columns:
  select_depara.append(build_case_when(column[1],column[0],"==",column[0]))

# COMMAND ----------

# All selects
all_selects = [*select_depara,*select_case_when_max,*select_cnpj_columns,*select_ocupacao,*select_atividade,*select_nao_sim]

# Get columns that should not apply "case when"
new_columns = df_censo_escolar.select(*all_selects).columns
other_columns = [column for column in df_censo_escolar.columns if column not in new_columns]

# Apply case when and select other columns
df_censo_escolar = df_censo_escolar.select(*other_columns,*all_selects)

# COMMAND ----------

# Base columns
select_base_columns = ["NU_ANO_CENSO"]

# Column to transform in struct
struct_dict = {
"ENDERECO_ESCOLA": ["NO_REGIAO","NO_UF","SG_UF","NO_MUNICIPIO","NO_MESORREGIAO","NO_MICRORREGIAO","TP_LOCALIZACAO","TP_LOCALIZACAO_DIFERENCIADA","DS_ENDERECO","NU_ENDERECO","DS_COMPLEMENTO","NO_BAIRRO","CO_CEP"],
"DADOS_ESCOLA": ["CO_ENTIDADE","NO_ENTIDADE","TP_DEPENDENCIA","TP_CATEGORIA_ESCOLA_PRIVADA","TP_SITUACAO_FUNCIONAMENTO","DT_ANO_LETIVO_INICIO","DT_ANO_LETIVO_TERMINO","IN_VINCULO_SECRETARIA_EDUCACAO","IN_VINCULO_SEGURANCA_PUBLICA","IN_VINCULO_SECRETARIA_SAUDE","IN_VINCULO_OUTRO_ORGAO","IN_CONVENIADA_PP","TP_CONVENIO_PODER_PUBLICO","IN_MANT_ESCOLA_PRIVADA_EMP","IN_MANT_ESCOLA_PRIVADA_ONG","IN_MANT_ESCOLA_PRIVADA_OSCIP","IN_MANT_ESCOLA_PRIV_ONG_OSCIP","IN_MANT_ESCOLA_PRIVADA_SIND","IN_MANT_ESCOLA_PRIVADA_SIST_S","IN_MANT_ESCOLA_PRIVADA_S_FINS","NU_CNPJ_ESCOLA_PRIVADA","NU_CNPJ_MANTENEDORA","TP_REGULAMENTACAO","TP_RESPONSAVEL_REGULAMENTACAO","IN_LOCAL_FUNC_PREDIO_ESCOLAR","TP_OCUPACAO_PREDIO_ESCOLAR","IN_FINAL_SEMANA"],
"TELEFONE_ESCOLA": ["NU_DDD", "NU_TELEFONE"],
"LOCAL_FUNCIONAMENTO": ["IN_LOCAL_FUNC_SALAS_EMPRESA","IN_LOCAL_FUNC_SOCIOEDUCATIVO","IN_LOCAL_FUNC_UNID_PRISIONAL","IN_LOCAL_FUNC_PRISIONAL_SOCIO","IN_LOCAL_FUNC_TEMPLO_IGREJA","IN_LOCAL_FUNC_CASA_PROFESSOR","IN_LOCAL_FUNC_GALPAO","TP_OCUPACAO_GALPAO","IN_LOCAL_FUNC_SALAS_OUTRA_ESC","IN_LOCAL_FUNC_OUTROS","IN_PREDIO_COMPARTILHADO"],
"ABASTECIMENTO_AGUA": ["IN_AGUA_FILTRADA","IN_AGUA_POTAVEL","IN_AGUA_REDE_PUBLICA","IN_AGUA_POCO_ARTESIANO","IN_AGUA_CACIMBA","IN_AGUA_FONTE_RIO","IN_AGUA_INEXISTENTE"],
"ABASTECIMENTO_ENERGIA": ["IN_ENERGIA_REDE_PUBLICA","IN_ENERGIA_GERADOR","IN_ENERGIA_GERADOR_FOSSIL","IN_ENERGIA_OUTROS","IN_ENERGIA_RENOVAVEL","IN_ENERGIA_INEXISTENTE"],
"ESGOTO_SANITARIO": ["IN_ESGOTO_REDE_PUBLICA","IN_ESGOTO_FOSSA_SEPTICA","IN_ESGOTO_FOSSA_COMUM","IN_ESGOTO_FOSSA","IN_ESGOTO_INEXISTENTE"],
"LIXO": ["IN_LIXO_SERVICO_COLETA","IN_LIXO_QUEIMA","IN_LIXO_ENTERRA","IN_LIXO_DESTINO_FINAL_PUBLICO","IN_LIXO_DESCARTA_OUTRA_AREA","IN_LIXO_JOGA_OUTRA_AREA","IN_LIXO_OUTROS","IN_LIXO_RECICLA","IN_TRATAMENTO_LIXO_SEPARACAO","IN_TRATAMENTO_LIXO_REUTILIZA","IN_TRATAMENTO_LIXO_RECICLAGEM","IN_TRATAMENTO_LIXO_INEXISTENTE"],
"INFRAESTRUTURA": ["IN_ALMOXARIFADO","IN_AREA_VERDE","IN_AUDITORIO","IN_BANHEIRO_FORA_PREDIO","IN_BANHEIRO_DENTRO_PREDIO","IN_BANHEIRO","IN_BANHEIRO_EI","IN_BANHEIRO_PNE","IN_BANHEIRO_FUNCIONARIOS","IN_BANHEIRO_CHUVEIRO","IN_BERCARIO","IN_BIBLIOTECA","IN_BIBLIOTECA_SALA_LEITURA","IN_COZINHA","IN_DESPENSA","IN_DORMITORIO_ALUNO","IN_DORMITORIO_PROFESSOR","IN_LABORATORIO_CIENCIAS","IN_LABORATORIO_INFORMATICA","IN_PATIO_COBERTO","IN_PATIO_DESCOBERTO","IN_PARQUE_INFANTIL","IN_PISCINA","IN_QUADRA_ESPORTES","IN_QUADRA_ESPORTES_COBERTA","IN_QUADRA_ESPORTES_DESCOBERTA","IN_REFEITORIO","IN_SALA_ATELIE_ARTES","IN_SALA_MUSICA_CORAL","IN_SALA_ESTUDIO_DANCA","IN_SALA_MULTIUSO","IN_SALA_DIRETORIA","IN_SALA_LEITURA","IN_SALA_PROFESSOR","IN_SALA_REPOUSO_ALUNO","IN_SECRETARIA","IN_SALA_ATENDIMENTO_ESPECIAL","IN_TERREIRAO","IN_VIVEIRO","IN_DEPENDENCIAS_PNE","IN_LAVANDERIA","IN_DEPENDENCIAS_OUTRAS","QT_SALAS_EXISTENTES","QT_SALAS_UTILIZADAS_DENTRO","QT_SALAS_UTILIZADAS_FORA","QT_SALAS_UTILIZADAS","QT_SALAS_UTILIZA_CLIMATIZADAS","QT_SALAS_UTILIZADAS_ACESSIVEIS","IN_ESPACO_ATIVIDADE","IN_ESPACO_EQUIPAMENTO"],
"RECURSOS_ACESSIBILIDADE": ["IN_ACESSIBILIDADE_CORRIMAO","IN_ACESSIBILIDADE_ELEVADOR","IN_ACESSIBILIDADE_PISOS_TATEIS","IN_ACESSIBILIDADE_VAO_LIVRE","IN_ACESSIBILIDADE_RAMPAS","IN_ACESSIBILIDADE_SINAL_SONORO","IN_ACESSIBILIDADE_SINAL_TATIL","IN_ACESSIBILIDADE_SINAL_VISUAL","IN_ACESSIBILIDADE_INEXISTENTE"],
"EQUIPAMENTOS": ["IN_EQUIP_PARABOLICA","IN_COMPUTADOR","IN_EQUIP_COPIADORA","IN_EQUIP_IMPRESSORA","IN_EQUIP_IMPRESSORA_MULT","IN_EQUIP_SCANNER","IN_EQUIP_NENHUM","IN_EQUIP_DVD","QT_EQUIP_DVD","IN_EQUIP_SOM","QT_EQUIP_SOM","IN_EQUIP_TV","QT_EQUIP_TV","IN_EQUIP_LOUSA_DIGITAL","QT_EQUIP_LOUSA_DIGITAL","IN_EQUIP_MULTIMIDIA","QT_EQUIP_MULTIMIDIA","IN_EQUIP_VIDEOCASSETE","IN_EQUIP_RETROPROJETOR","IN_EQUIP_FAX","IN_EQUIP_FOTO","QT_EQUIP_VIDEOCASSETE","QT_EQUIP_PARABOLICA","QT_EQUIP_COPIADORA","QT_EQUIP_RETROPROJETOR","QT_EQUIP_IMPRESSORA","QT_EQUIP_IMPRESSORA_MULT","QT_EQUIP_FAX","QT_EQUIP_FOTO","QT_COMP_ALUNO","IN_DESKTOP_ALUNO","QT_DESKTOP_ALUNO","IN_COMP_PORTATIL_ALUNO","QT_COMP_PORTATIL_ALUNO","IN_TABLET_ALUNO","QT_TABLET_ALUNO","QT_COMPUTADOR","QT_COMP_ADMINISTRATIVO","IN_ACESSO_INTERNET_COMPUTADOR","IN_ACES_INTERNET_DISP_PESSOAIS","TP_REDE_LOCAL","IN_BANDA_LARGA"],
"INTERNET": ["IN_INTERNET","IN_INTERNET_ALUNOS","IN_INTERNET_ADMINISTRATIVO","IN_INTERNET_APRENDIZAGEM","IN_INTERNET_COMUNIDADE","IN_REDES_SOCIAIS"],
"PROFISSIONAIS": ["QT_FUNCIONARIOS","IN_PROF_ADMINISTRATIVOS","QT_PROF_ADMINISTRATIVOS","IN_PROF_SERVICOS_GERAIS","QT_PROF_SERVICOS_GERAIS","IN_PROF_BIBLIOTECARIO","QT_PROF_BIBLIOTECARIO","IN_PROF_SAUDE","QT_PROF_SAUDE","IN_PROF_COORDENADOR","QT_PROF_COORDENADOR","IN_PROF_FONAUDIOLOGO","QT_PROF_FONAUDIOLOGO","IN_PROF_NUTRICIONISTA","QT_PROF_NUTRICIONISTA","IN_PROF_PSICOLOGO","QT_PROF_PSICOLOGO","IN_PROF_ALIMENTACAO","QT_PROF_ALIMENTACAO","IN_PROF_PEDAGOGIA","QT_PROF_PEDAGOGIA","IN_PROF_SECRETARIO","QT_PROF_SECRETARIO","IN_PROF_SEGURANCA","QT_PROF_SEGURANCA","IN_PROF_MONITORES","QT_PROF_MONITORES","IN_PROF_GESTAO","QT_PROF_GESTAO","IN_PROF_ASSIST_SOCIAL","QT_PROF_ASSIST_SOCIAL"],
"ALIMENTACAO": ["IN_ALIMENTACAO"],
"FORMA_ORGANIZACAO": ["IN_SERIE_ANO","IN_PERIODOS_SEMESTRAIS","IN_FUNDAMENTAL_CICLOS","IN_GRUPOS_NAO_SERIADOS","IN_MODULOS","IN_FORMACAO_ALTERNANCIA"],
"MATERIAL": ["IN_MATERIAL_PED_MULTIMIDIA","IN_MATERIAL_PED_INFANTIL","IN_MATERIAL_PED_CIENTIFICO","IN_MATERIAL_PED_DIFUSAO","IN_MATERIAL_PED_MUSICAL","IN_MATERIAL_PED_JOGOS","IN_MATERIAL_PED_ARTISTICAS","IN_MATERIAL_PED_DESPORTIVA","IN_MATERIAL_PED_INDIGENA","IN_MATERIAL_PED_ETNICO","IN_MATERIAL_PED_CAMPO","IN_MATERIAL_PED_NENHUM","IN_MATERIAL_ESP_QUILOMBOLA","IN_MATERIAL_ESP_INDIGENA","IN_MATERIAL_ESP_NAO_UTILIZA"],
"EDUCAO_INDIGENA": ["IN_EDUCACAO_INDIGENA","TP_INDIGENA_LINGUA","CO_LINGUA_INDIGENA_1","CO_LINGUA_INDIGENA_2","CO_LINGUA_INDIGENA_3"],
"ENSINO": ["IN_BRASIL_ALFABETIZADO","IN_EXAME_SELECAO","IN_BAS","IN_INF","IN_INF_CRE","IN_INF_PRE","IN_FUND","IN_FUND_AI","IN_FUND_AF","IN_MED","IN_PROF","IN_PROF_TEC","IN_EJA","IN_EJA_FUND","IN_EJA_MED","IN_ESP","IN_ESP_CC","IN_ESP_CE"],
"RESERVA_VAGAS": ["IN_RESERVA_PPI","IN_RESERVA_RENDA","IN_RESERVA_PUBLICA","IN_RESERVA_PCD","IN_RESERVA_OUTROS","IN_RESERVA_NENHUMA"],
"ORGAOS_COLEGIADOS": ["IN_ORGAO_ASS_PAIS","IN_ORGAO_ASS_PAIS_MESTRES","IN_ORGAO_CONSELHO_ESCOLAR","IN_ORGAO_GREMIO_ESTUDANTIL","IN_ORGAO_OUTROS","IN_ORGAO_NENHUM"],
"PEGADOGIA": ["TP_PROPOSTA_PEDAGOGICA","TP_AEE","TP_ATIVIDADE_COMPLEMENTAR","IN_MEDIACAO_PRESENCIAL","IN_MEDIACAO_SEMIPRESENCIAL","IN_MEDIACAO_EAD","IN_REGULAR"],
"TURNO": ["IN_DIURNO", "IN_NOTURNO", "IN_EAD"],
"MATRICULA": ["QT_MAT_BAS","QT_MAT_INF","QT_MAT_INF_CRE","QT_MAT_INF_PRE","QT_MAT_FUND","QT_MAT_FUND_AI","QT_MAT_FUND_AF","QT_MAT_MED","QT_MAT_PROF","QT_MAT_PROF_TEC","QT_MAT_EJA","QT_MAT_EJA_FUND","QT_MAT_EJA_MED","QT_MAT_ESP","QT_MAT_ESP_CC","QT_MAT_ESP_CE","QT_MAT_BAS_FEM","QT_MAT_BAS_MASC","QT_MAT_BAS_ND","QT_MAT_BAS_BRANCA","QT_MAT_BAS_PRETA","QT_MAT_BAS_PARDA","QT_MAT_BAS_AMARELA","QT_MAT_BAS_INDIGENA","QT_MAT_BAS_0_3","QT_MAT_BAS_4_5","QT_MAT_BAS_6_10","QT_MAT_BAS_11_14","QT_MAT_BAS_15_17","QT_MAT_BAS_18_MAIS","QT_MAT_BAS_D","QT_MAT_BAS_N","QT_MAT_BAS_EAD","QT_MAT_INF_INT","QT_MAT_INF_CRE_INT","QT_MAT_INF_PRE_INT","QT_MAT_FUND_INT","QT_MAT_FUND_AI_INT","QT_MAT_FUND_AF_INT","QT_MAT_MED_INT"],
"DOCENTES": ["QT_DOC_BAS","QT_DOC_INF","QT_DOC_INF_CRE","QT_DOC_INF_PRE","QT_DOC_FUND","QT_DOC_FUND_AI","QT_DOC_FUND_AF","QT_DOC_MED","QT_DOC_PROF","QT_DOC_PROF_TEC","QT_DOC_EJA","QT_DOC_EJA_FUND","QT_DOC_EJA_MED","QT_DOC_ESP","QT_DOC_ESP_CC","QT_DOC_ESP_CE"],
"TURMAS": ["QT_TUR_BAS","QT_TUR_INF","QT_TUR_INF_CRE","QT_TUR_INF_PRE","QT_TUR_FUND","QT_TUR_FUND_AI","QT_TUR_FUND_AF","QT_TUR_MED","QT_TUR_PROF","QT_TUR_PROF_TEC","QT_TUR_EJA","QT_TUR_EJA_FUND","QT_TUR_EJA_MED","QT_TUR_ESP","QT_TUR_ESP_CC","QT_TUR_ESP_CE"]
}
select_struct = [f.struct(*struct_dict[k]).alias(k) for k in struct_dict]

# Apply
df_censo_escolar = df_censo_escolar.select(*select_base_columns,*select_struct)

# Rename column
df_censo_escolar = df_censo_escolar.withColumnRenamed("NU_ANO_CENSO","ANO_CENSO")

# COMMAND ----------

# Save
(
  df_censo_escolar
  .write
  .format("delta")
  .mode("overwrite")
  .option("replaceWhere","ANO_CENSO == {}".format(year))
  .partitionBy("ANO_CENSO")
  .save("")
)