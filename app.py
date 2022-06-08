import datetime
import re
import streamlit as st
import rdflib
from rdflib.graph import Graph
from rdflib import URIRef, BNode, Literal
from rdflib import Namespace
from rdflib.namespace import CSVW, DC, DCAT, DCTERMS, DOAP, FOAF, ODRL2, ORG, OWL, PROF, PROV, RDF, RDFS, SDO, SH, SKOS, SOSA, SSN, TIME, VOID, XMLNS, XSD
from rdflib.plugins import sparql
import owlrl
from SPARQLWrapper import SPARQLWrapper, JSON, XML, N3, TURTLE, JSONLD
import unicodedata
from texthero import preprocessing
import texthero as hero
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import pandas
from difflib import SequenceMatcher
from semanticscholar import SemanticScholar
import requests
import json
from bs4 import BeautifulSoup
from scholarly import scholarly

@st.cache()
def buscaScholar(autor):
  dados = []
  search_query = scholarly.search_author(autor)
  for x in search_query:
      dados.append(scholarly.fill(x, sections=['basics', 'indices','publications']))
  return dados
@st.cache()
def buscaInfo(autor,posicao):
  date = datetime.date.today()
  year = int(date.strftime("%Y")) - 5
  autor_dados = scholarly.fill(autor[posicao])
  publicacoes = autor_dados['publications']
  informacoes = autor_dados
  publi= [] 
  for p in publicacoes:
    if not 'pub_year' in  p['bib']:
          p['bib']['pub_year'] = '0000'
    if int(p['bib']['pub_year']) >= year: 
      publi.append(scholarly.fill(p))

  Autor_Info = {
 'nome' : informacoes['name'] ,
 'afilicao' : informacoes['affiliation'],
 'interesse' : informacoes['interests'],
 'hindex' : informacoes['hindex'] ,
 'i10' : informacoes['i10index'] ,
 'citado' : informacoes['citedby'] ,
 'publicacao' : [] ,
  }
  for x in publi:
    if "journal" in x['bib']:
        if 'pub_year' in  x['bib']:
          ano  = x['bib']['pub_year']
        else:
          ano = '0000'  
        Autor_Info['publicacao'].append({
                  'title':  x['bib']['title'],
                  'pub_year': ano ,
                  'tipo_publi': 'journal'  ,
                  'veiculo':  x['bib']['journal'],})

    if "conference" in x['bib']:
        if 'pub_year' in  x['bib']:
          ano  = x['bib']['pub_year']
        else:
          ano = '0000'  
        Autor_Info['publicacao'].append({
                  'title':  x['bib']['title'],
                  'pub_year': ano ,
                  'tipo_publi': 'conference'  ,
                  'veiculo':  x['bib']['conference'],})

    if "Book" in x['bib']:
        if 'pub_year' in  x['bib']:
          ano  = x['bib']['pub_year']
        else:
          ano = '0000'
        Autor_Info['publicacao'].append({
                  'title':  x['bib']['title'],
                  'pub_year':  ano ,
                  'tipo_publi': 'Book'  ,
                  'veiculo':  x['bib']['Book'],})

    if "volume" in x['bib']:
        if 'pub_year' in  x['bib']:
          ano  = x['bib']['pub_year']
        else:
          ano = '0000'
        Autor_Info['publicacao'].append({
                  'title':  x['bib']['title'],
                  'pub_year':  ano ,
                  'tipo_publi': 'volume'  ,
                  'veiculo':  x['bib']['volume'],})
        
  for t in Autor_Info['publicacao']:
    if t['veiculo'].isdigit() == True:
      del(Autor_Info['publicacao'][Autor_Info['publicacao'].index(t)])
  del informacoes["publications"]

  return Autor_Info

def buscaSemantic(Autor_Info):
    titulos = []
    sch = SemanticScholar(timeout=5)
    for t in Autor_Info['publicacao']:
        if_contains_t = t['title']
        headers = {'Accept': 'application/json'}
        r = \
            requests.get('https://api.semanticscholar.org/graph/v1/paper/search?query='
                          + if_contains_t + '&fields=title,authors',
                         headers=headers)
        data = r.json()
        #if data['total'] >= 1:
        for x in data['data'][0]['authors']:
                    result = SequenceMatcher(None, x['name'],
                            Autor_Info['nome']).ratio()
                    if result > 0.6:
                        semantic_dados = sch.author(x['authorId'])
        
                        for t in Autor_Info['publicacao']:
                            titulos.append(t['title'].lower())

                        for t in semantic_dados['papers']:
                            match = process.extract(t['title'].lower(), titulos,
                                                    scorer=fuzz.token_sort_ratio)
                            if match[0][1] < 60:
                                paperid = str(t['paperId'])
                                paper = sch.paper(paperid)
                                Autor_Info['publicacao'].append({'title': paper['title'],
                                        'pub_year': paper['year'], 'veiculo': paper['venue'
                                        ]})
                                
                    return Autor_Info
                    break
def qualis (Autor_Info):

  _pr = pandas.read_csv('https://docs.google.com/spreadsheets/d/e/2PACX-1vRqi1UUf_cTEj1B4VWMCHk3fhzcMQgsyH3jSox1m-G6CuOuUniUuLc8GK6yjMY4CnUWZd_V77sCuYut/pub?output=csv')
  _pr['Área de Avaliação'] = _pr['Área de Avaliação'].str.strip()
  _pr['Área de Avaliação'].tolist()
  _pr['Estrato'] = _pr['Estrato'].str.strip()
  _pr['Estrato'].tolist()
  
  pr = _pr.loc[_pr['Área de Avaliação'].values == 'CIÊNCIA DA COMPUTAÇÃO'] 
  pr = pr.reset_index(drop=True)

  cn = pandas.read_csv('https://docs.google.com/spreadsheets/d/e/2PACX-1vT7FcK0i4UN6ULcLFlEa7FO2E0vemz-9VfIwEtaOW6PnP4eAzCyzJ1BPwtATk0ZKUKVBvHaT5Mx2TBV/pub?output=csv')







  #conferencia_link = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vTZsntDnttAWGHA8NZRvdvK5A_FgOAQ_tPMzP7UUf-CHwF_3PHMj_TImyXN2Q_Tmcqm2MqVknpHPoT2/pubhtml?gid=0&single=true'
  #res = requests.get(conferencia_link)
  #soup = BeautifulSoup(res.content, 'lxml')
  #conferencias = pandas.read_html(str(soup))
  #c = {'sigla': conferencias[0]['Unnamed: 1'],
      #    'conferencia': conferencias[0]['Unnamed: 2'],
       #   'Qualis_Final': conferencias[0]['Unnamed: 7']}
  #cn = pandas.DataFrame(data=c)

  #cn = pandas.DataFrame(data=c).dropna()

  #cn = cn.drop(0)
 # pr = pr.drop(0)

  custom_pipeline = [preprocessing.fillna, 
                        preprocessing.lowercase,
                        preprocessing.remove_whitespace,
                        preprocessing.remove_punctuation]
  cn['conferencia_limpo'] = hero.clean(cn['conferencia'],
              custom_pipeline)
  pr['periodicos_limpo'] = hero.clean(pr['Título'],
              custom_pipeline)

  con = cn['conferencia_limpo'].values.tolist()
  per = pr['periodicos_limpo'].values.tolist()

  for i in Autor_Info['publicacao']:

          
          peri = process.extractOne(i['veiculo'],
                                   pr['periodicos_limpo'],
                                    scorer=fuzz.token_set_ratio)
          conf = process.extractOne(i['veiculo'],
                                    cn['conferencia_limpo'],
                                    scorer=fuzz.token_set_ratio)

          
          if peri[1] > conf[1] : 
            if peri[1] >= 95:
                df_mask=pr['periodicos_limpo'] == str(peri[0])
                filtered_df = pr[df_mask]
                i['Qualis'] = str(filtered_df.iat[0,3])
                #i['veiculo'] = str(filtered_df.iat[0,1])
                i['inss'] = str(filtered_df.iat[0,0])
                i['tipo_evento'] = 'periodico'
          else:
            if conf[1] >= 95:
              df_mask=cn['conferencia_limpo'] == str(conf[0])
              filtered_df = cn[df_mask]
              i['Qualis'] = str(filtered_df.iat[0,6])
              #i['veiculo'] = str(filtered_df.iat[0,3])
              i['sigla'] = str(filtered_df.iat[0,0])
              i['tipo_evento'] = 'conferencia'

  return Autor_Info  
def clear_char(palavra):

    # Unicode normalize transforma um caracter em seu equivalente em latin.
    nfkd = unicodedata.normalize('NFKD', palavra)
    palavraSemAcento = u"".join([c for c in nfkd if not unicodedata.combining(c)])

    # Usa expressão regular para retornar a palavra apenas com números, letras e espaço
    return re.sub('[^a-zA-Z0-9 \\\]', '', palavraSemAcento)


def gera_ontologia(base_principal):
  date = datetime.date.today()
  year = str(int(date.strftime("%Y")) - 5) 
  dic={}
  p = []
  e= []
  g = Graph()
  n3data = """@prefix : <http://www.semanticweb.org/fantasma/ontologies/2021/10/Publicacao#> .
  @prefix owl: <http://www.w3.org/2002/07/owl#> .
  @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
  @prefix xml: <http://www.w3.org/XML/1998/nomespace> .
  @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
  @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
  @base <http://www.semanticweb.org/fantasma/ontologies/2021/10/Publicacao> .

  <http://www.semanticweb.org/fantasma/ontologies/2021/10/Publicacao> rdf:type owl:Ontology .

  #################################################################
  #    Object Properties
  #################################################################

  ###  http://www.semanticweb.org/fantasma/ontologies/2021/10/Publicacao#Afiliado
  :Afiliado rdf:type owl:ObjectProperty ;
            rdfs:domain :Autor_Cientifico ;
            rdfs:range :Instituicao .


  ###  http://www.semanticweb.org/fantasma/ontologies/2021/10/Publicacao#Classificada
  :Classificada rdf:type owl:ObjectProperty ;
                rdfs:domain :Veiculo ;
                rdfs:range :Qualis .


  ###  http://www.semanticweb.org/fantasma/ontologies/2021/10/Publicacao#Detem
  :Detem rdf:type owl:ObjectProperty ;
        rdfs:domain :Autor_Cientifico ;
        rdfs:range :Autoria_Cientifica .


  ###  http://www.semanticweb.org/fantasma/ontologies/2021/10/Publicacao#Pesquisa
  :Pesquisa rdf:type owl:ObjectProperty ;
            rdfs:domain :Autor_Cientifico ;
            rdfs:range :Area_Pesquisa .


  ###  http://www.semanticweb.org/fantasma/ontologies/2021/10/Publicacao#Publicado_em
  :Publicado_em rdf:type owl:ObjectProperty ;
                rdfs:domain :Publicacao ;
                rdfs:range :Veiculo .


  ###  http://www.semanticweb.org/fantasma/ontologies/2021/10/Publicacao#Refere_se
  :Refere_se rdf:type owl:ObjectProperty ;
            rdfs:domain :Autoria_Cientifica ;
            rdfs:range :Texto_Autoral_Cientifico_Publicado .


  ###  http://www.semanticweb.org/fantasma/ontologies/2021/10/Publicacao#Submetido
  :Submetido rdf:type owl:ObjectProperty ;
            rdfs:domain :Texto_Autoral_Cientifico_Publicado ;
            rdfs:range :Publicacao .


  #################################################################
  #    Data properties
  #################################################################

  ###  http://www.semanticweb.org/fantasma/ontologies/2021/10/Publicacao#Area_Pesquisa
  :Area_Pesquisa rdf:type owl:DatatypeProperty ;
                rdfs:domain :Area_Pesquisa .


  ###  http://www.semanticweb.org/fantasma/ontologies/2021/10/Publicacao#Autor_Citacao
  :Autor_Citacao rdf:type owl:DatatypeProperty ;
                rdfs:domain :Autor_Cientifico .


  ###  http://www.semanticweb.org/fantasma/ontologies/2021/10/Publicacao#Autor_IndiceH
  :Autor_IndiceH rdf:type owl:DatatypeProperty ;
                rdfs:domain :Autor_Cientifico .


  ###  http://www.semanticweb.org/fantasma/ontologies/2021/10/Publicacao#Autor_indiceI10
  :Autor_indiceI10 rdf:type owl:DatatypeProperty ;
                  rdfs:domain :Autor_Cientifico .


  ###  http://www.semanticweb.org/fantasma/ontologies/2021/10/Publicacao#Edicao_Ano
  :Edicao_Ano rdf:type owl:DatatypeProperty ;
              rdfs:domain :Veiculo .


  ###  http://www.semanticweb.org/fantasma/ontologies/2021/10/Publicacao#Edicao_Nome
  :Edicao_Nome rdf:type owl:DatatypeProperty ;
              rdfs:domain :Veiculo .


  ###  http://www.semanticweb.org/fantasma/ontologies/2021/10/Publicacao#Edicao_Tipo
  :Edicao_Tipo rdf:type owl:DatatypeProperty ;
              rdfs:domain :Veiculo .


  ###  http://www.semanticweb.org/fantasma/ontologies/2021/10/Publicacao#Instituicao
  :Instituicao rdf:type owl:DatatypeProperty ;
              rdfs:domain :Instituicao .


  ###  http://www.semanticweb.org/fantasma/ontologies/2021/10/Publicacao#Nome_Autor
  :Nome_Autor rdf:type owl:DatatypeProperty ;
              rdfs:domain :Autor_Cientifico .


  ###  http://www.semanticweb.org/fantasma/ontologies/2021/10/Publicacao#Publicacao_Citacao
  :Publicacao_Citacao rdf:type owl:DatatypeProperty ;
                      rdfs:domain :Publicacao .


  ###  http://www.semanticweb.org/fantasma/ontologies/2021/10/Publicacao#Qualis_Extrato
  :Qualis_Extrato rdf:type owl:DatatypeProperty ;
                  rdfs:domain :Qualis .


  ###  http://www.semanticweb.org/fantasma/ontologies/2021/10/Publicacao#Titulo_Artigo
  :Titulo_Artigo rdf:type owl:DatatypeProperty ;
                rdfs:domain :Texto .


  ###  http://www.semanticweb.org/fantasma/ontologies/2021/10/Publicacao#Veiculo_Codigo
  :Veiculo_Codigo rdf:type owl:DatatypeProperty ;
                  rdfs:domain :Veiculo .


  #################################################################
  #    Classes
  #################################################################

  ###  http://www.semanticweb.org/fantasma/ontologies/2021/10/Publicacao#Area_Pesquisa
  :Area_Pesquisa rdf:type owl:Class .


  ###  http://www.semanticweb.org/fantasma/ontologies/2021/10/Publicacao#Autor_Cientifico
  :Autor_Cientifico rdf:type owl:Class ;
                    rdfs:subClassOf :Pessoa .


  ###  http://www.semanticweb.org/fantasma/ontologies/2021/10/Publicacao#Autoria_Cientifica
  :Autoria_Cientifica rdf:type owl:Class .


  ###  http://www.semanticweb.org/fantasma/ontologies/2021/10/Publicacao#Instituicao
  :Instituicao rdf:type owl:Class .


  ###  http://www.semanticweb.org/fantasma/ontologies/2021/10/Publicacao#Pessoa
  :Pessoa rdf:type owl:Class .


  ###  http://www.semanticweb.org/fantasma/ontologies/2021/10/Publicacao#Publicacao
  :Publicacao rdf:type owl:Class .


  ###  http://www.semanticweb.org/fantasma/ontologies/2021/10/Publicacao#Qualis
  :Qualis rdf:type owl:Class .


  ###  http://www.semanticweb.org/fantasma/ontologies/2021/10/Publicacao#Texto
  :Texto rdf:type owl:Class .


  ###  http://www.semanticweb.org/fantasma/ontologies/2021/10/Publicacao#Texto_Autoral_Cientifico_Publicado
  :Texto_Autoral_Cientifico_Publicado rdf:type owl:Class ;
                                      rdfs:subClassOf :Texto .


  ###  http://www.semanticweb.org/fantasma/ontologies/2021/10/Publicacao#Veiculo
  :Veiculo rdf:type owl:Class .


  #################################################################
  #    Individuals
  #################################################################

  ###  http://www.semanticweb.org/fantasma/ontologies/2021/10/Publicacao#A1
  :A1 rdf:type owl:nomedIndividual ,
              :Qualis ;
      :Qualis_Extrato "A1" .


  ###  http://www.semanticweb.org/fantasma/ontologies/2021/10/Publicacao#A2
  :A2 rdf:type owl:NamedIndividual ,
              :Qualis ;
      :Qualis_Extrato "A2" .


  ###  http://www.semanticweb.org/fantasma/ontologies/2021/10/Publicacao#A3
  :A3 rdf:type owl:NamedIndividual ,
              :Qualis ;
      :Qualis_Extrato "A3" .


  ###  http://www.semanticweb.org/fantasma/ontologies/2021/10/Publicacao#A4
  :A4 rdf:type owl:NamedIndividual ,
              :Qualis ;
      :Qualis_Extrato "A4" .


  ###  http://www.semanticweb.org/fantasma/ontologies/2021/10/Publicacao#B1
  :B1 rdf:type owl:NamedIndividual ,
              :Qualis ;
      :Qualis_Extrato "B1" .


  ###  http://www.semanticweb.org/fantasma/ontologies/2021/10/Publicacao#B2
  :B2 rdf:type owl:NamedIndividual ,
              :Qualis ;
      :Qualis_Extrato "B2" .


  ###  http://www.semanticweb.org/fantasma/ontologies/2021/10/Publicacao#B3
  :B3 rdf:type owl:NamedIndividual ,
              :Qualis ;
      :Qualis_Extrato "B3" .


  ###  http://www.semanticweb.org/fantasma/ontologies/2021/10/Publicacao#B4
  :B4 rdf:type owl:NamedIndividual ,
              :Qualis ;
      :Qualis_Extrato "B4" .


  ###  http://www.semanticweb.org/fantasma/ontologies/2021/10/Publicacao#C
  :C rdf:type owl:NamedIndividual ,
              :Qualis ;
    :Qualis_Extrato "C" .


  ###  Generated by the OWL API (version 4.5.9.2019-02-01T07:24:44Z) https://github.com/owlcs/owlapi


  """
  
  ontologia = g.parse(data=n3data, format='ttl')
  pp  = Namespace("http://www.semanticweb.org/fantasma/ontologies/2021/10/Publicacao#")#iri
  g.bind("pp", pp )
  nome_autor = base_principal['nome']
  Interesses_autor = base_principal['interesse']
  Afiliação_autor = base_principal['afilicao']
  nome_autor_limpo = re.sub('[,|\s]+', '_', clear_char(nome_autor))
  Afiliacao_autor_limpo = re.sub('[,|\s]+', '_', clear_char(Afiliação_autor))

  #dados do autor 
  g.add((pp[nome_autor_limpo], RDF.type, pp.Autor_Cientifico))
  g.add((pp[nome_autor_limpo], pp.Nome_Autor, Literal(base_principal['nome'])))
  g.add((pp[nome_autor_limpo], pp.Autor_Citacao, Literal(base_principal['citado'])))
  g.add((pp[nome_autor_limpo], pp.Autor_IndiceH, Literal(base_principal['hindex'])))
  g.add((pp[nome_autor_limpo], pp.Autor_indiceI10, Literal(base_principal['i10'])))


  g.add((pp[Afiliacao_autor_limpo], RDF.type, pp.Instituicao))
  g.add((pp[Afiliacao_autor_limpo], pp.Instituicao, Literal(Afiliação_autor)))

  g.add((pp[nome_autor_limpo], pp.Afiliado, pp[Afiliacao_autor_limpo]))

  #area de interesse
  for x in Interesses_autor:
      area = re.sub('[,|\s]+', '_', clear_char(x))

      g.add((pp[area], RDF.type, pp.Area_Pesquisa))
      g.add((pp[area], pp.Area_Pesquisa, Literal(x)))
      g.add((pp[nome_autor_limpo], pp.Pesquisa, pp[area]))

  #publicacao

      
    
  for x in range(len(base_principal['publicacao'])):
      titulo = base_principal['publicacao'][x]['title']
      titulo_clean = re.sub('[,|\s]+', '_', clear_char(titulo))
      veiculo =  base_principal['publicacao'][x]['veiculo']
      veiculo_clean = re.sub('[,|\s]+', '_', clear_char( veiculo))
      autoria = nome_autor_limpo +'_Autoria_'+str(x)
      publicacao = nome_autor_limpo +'_Publicacao_'+str(x)
     
      #Cria Autoria 
      g.add((pp[autoria], RDF.type, pp.Autoria_Cientifica))
      g.add((pp[nome_autor_limpo], pp.Detem, pp[autoria]))
      
      #Cria Artigo
      g.add((pp[titulo_clean], RDF.type, pp.Texto_Autoral_Cientifico_Publicado))
      g.add((pp[titulo_clean], pp.Titulo_Artigo, Literal(titulo)))

      g.add((pp[autoria], pp.Refere_se, pp[titulo_clean]))
      #Cria Publicacao 
      g.add((pp[publicacao], RDF.type, pp.Publicacao))
      g.add((pp[titulo_clean], pp.Submetido, pp[publicacao]))
      g.add((pp[veiculo_clean], RDF.type, pp.Veiculo))
      g.add((pp[veiculo_clean], pp.Edicao_Ano, Literal(base_principal['publicacao'][x]['pub_year'])))
      g.add((pp[veiculo_clean], pp.Edicao_Nome, Literal(veiculo)))
      g.add((pp[publicacao], pp.Publicado_em , pp[veiculo_clean]))  


      if 'Qualis' in base_principal['publicacao'][x]:
          qualis = base_principal['publicacao'][x]['Qualis']
          #qualis_clear = re.sub('[,|\s]+', '_', clear_char(qualis))
          g.add((pp[veiculo_clean], pp.Classificada, pp[qualis]))
          g.add((pp[veiculo_clean], pp.Edicao_Tipo, Literal(base_principal['publicacao'][x]['tipo_publi'])))
      else: 
          #g.add((pp[veiculo_clean], pp.Classificada, pp["C"]))
          g.add((pp[veiculo_clean], pp.Edicao_Tipo, Literal('Não Especificado')))


  #g.serialize(data = ontologia, format='turtle')
  qres = g.query(
    """SELECT ?titulo ?q ?evento ?tipo
      WHERE
        { 
         ?artigo a pp:Texto_Autoral_Cientifico_Publicado;
              pp:Titulo_Artigo ?titulo.
         ?artigo pp:Submetido ?y.
          ?y pp:Publicado_em ?evento.
          ?evento  pp:Edicao_Tipo ?tipo.
          ?evento  pp:Edicao_Ano ?data.
            FILTER (?data >= """+year+""")
          ?evento pp:Classificada ?qualis.
         ?qualis pp:Qualis_Extrato ?q.
         }""")
  
  #Colocar filtro por nome.
  #SELECT ?titulo ?q ?evento ?tipo
      #WHERE
        #{ 
        # ?artigo a pp:Texto_Autoral_Cientifico_Publicado;
          #    pp:Titulo_Artigo ?titulo.
        # ?artigo pp:Submetido ?y.
          #?y pp:Publicado_em ?evento.
          #?evento  pp:Edicao_Tipo ?tipo.  
          #?evento pp:Classificada ?qualis.
        # ?qualis pp:Qualis_Extrato ?q.}

  for row in qres:
        d = {
        'Titulo' : re.search("([^']*)",str(row.titulo)).string,
        'Evento': re.search("([^']*)",str(row.evento)).string,
        'Tipo' : re.search("([^']*)",str(row.tipo)).string,
        'Qualis': re.search("([^']*)",str(row.q)).string,}
        p.append(d)
  for x in range(len(p)):
        if p[x]['Tipo'] == 'journal' :
            if  p[x]['Qualis'] == 'A1':
                p[x][ 'Pontuação'] = 1.000

            if p[x]['Qualis'] == 'A2':
                p[x][ 'Pontuação'] =  0.875

            if p[x]['Qualis'] == 'A3':
                p[x][ 'Pontuação'] = 0.750

            if p[x]['Qualis'] == 'A4':
                p[x][ 'Pontuação'] =  0.625

            if p[x]['Qualis'] == 'B1':
                p[x][ 'Pontuação'] =  0.500

            if p[x]['Qualis'] == 'B2':
                p[x][ 'Pontuação'] = 0.200

            if p[x]['Qualis'] == 'B3':
                d[ 'Pontuação'] =  0.100

            if p[x]['Qualis'] == 'B4':
                p[x][ 'Pontuação'] =  0.050
            if p[x]['Qualis'] == 'C':
                p[x][ 'Pontuação'] =  0.000   
        if p[x]['Tipo'] == 'conference':
            if p[x]['Qualis'] == 'A1':
                p[x][ 'Pontuação'] = 1.000
              
            if p[x]['Qualis'] == 'A2':
                p[x][ 'Pontuação'] =  0.875

            if p[x]['Qualis'] == 'A3':
                p[x][ 'Pontuação'] = 0.750

            if p[x]['Qualis'] == 'A4':
                p[x][ 'Pontuação'] =  0.625

            if p[x]['Qualis'] == 'B1':
                p[x][ 'Pontuação'] =  0.500

            if p[x]['Qualis'] == 'B2':
                p[x][ 'Pontuação'] = 0.200

            if p[x]['Qualis'] == 'B3':
                p[x][ 'Pontuação'] = 0.100

            if p[x]['Qualis'] == 'B4':
                p[x][ 'Pontuação'] =  0.050
            if p[x]['Qualis'] == 'C':
                p[x][ 'Pontuação'] =  0.000   

  data_qualis = pandas.DataFrame(data=p)
  s = g.serialize(format='turtle')

  return data_qualis   
def Executa():
  autor= []
  autor_name = []

  Autor = st.text_input(label='Nome do Pesquisador')
  autor = buscaScholar(Autor)
  for x in range(len(autor)):
    autor_name.append(autor[x]['name'])
  escolha = st.selectbox('Pesquisadores', autor_name)  
  if st.button(label='Buscar'):
    i = autor_name.index(escolha)
    info = buscaInfo(autor,i)
    semantic = buscaSemantic(info)
    base_principal = qualis(semantic)
    tabela = gera_ontologia(base_principal)
    st.dataframe(tabela)
def main():
  Executa()

main()      
