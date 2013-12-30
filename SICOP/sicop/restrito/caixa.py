from django.contrib.auth.decorators import login_required, permission_required,\
    user_passes_test
from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext
from sicop.models import Tbcaixa, Tbtipocaixa, AuthUser, Tbprocessobase,\
    Tbpecastecnicas, Tbprocessorural, Tbprocessoclausula, Tbprocessourbano
from django.http import HttpResponseRedirect
from django.contrib import messages
from sicop.forms import FormCaixa
from sicop.relatorio_base import relatorio_pdf_base_consulta,\
    relatorio_ods_base_header, relatorio_ods_base, relatorio_csv_base
from reportlab.platypus.paragraph import Paragraph
from reportlab.platypus.flowables import Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY
from sicop.admin import verificar_permissao_grupo
from django.http.response import HttpResponse
from odslib import ODS
import csv

@login_required
def consulta(request):
    if request.method == "POST":
        nome = request.POST['nmlocalarquivo']
        lista = Tbcaixa.objects.all().filter( nmlocalarquivo__icontains=nome, tbtipocaixa__tbdivisao__id = AuthUser.objects.get( pk = request.user.id ).tbdivisao.id )
    else:
        lista = Tbcaixa.objects.all().filter( tbtipocaixa__tbdivisao__id = AuthUser.objects.get( pk = request.user.id ).tbdivisao.id )
    lista = lista.order_by( 'id' )
    
    #gravando na sessao o resultado da consulta preparando para o relatorio/pdf
    request.session['relatorio_caixa'] = lista
    return render_to_response('sicop/restrito/caixa/consulta.html' ,{'lista':lista}, context_instance = RequestContext(request))

@login_required
@user_passes_test( lambda u: verificar_permissao_grupo(u, {'Super','Administrador'}), login_url='/excecoes/permissao_negada/')
def cadastro(request):
    tipocaixa = Tbtipocaixa.objects.all().filter( tbdivisao__id = AuthUser.objects.get( pk = request.user.id ).tbdivisao.id )
    if request.method == "POST":
        next = request.GET.get('next', '/')
        form = FormCaixa(request.POST)
        if validacao(request):
            if form.is_valid():
                form.save()
                if next == "/":
                    return HttpResponseRedirect("/sicop/restrito/caixa/consulta/")
                else:    
                    return HttpResponseRedirect( next ) 
    else:
        form = FormCaixa()
    return render_to_response('sicop/restrito/caixa/cadastro.html',{"form":form,"tipocaixa":tipocaixa}, context_instance = RequestContext(request))

@login_required
@user_passes_test( lambda u: verificar_permissao_grupo(u, {'Super','Administrador'}), login_url='/excecoes/permissao_negada/')
def edicao(request, id):
    tipocaixa = Tbtipocaixa.objects.all().filter( tbdivisao__id = AuthUser.objects.get( pk = request.user.id ).tbdivisao.id )
    instance = get_object_or_404(Tbcaixa, id=id)
    if request.method == "POST":
        form = FormCaixa(request.POST,request.FILES,instance=instance)
        if validacao(request):
            if form.is_valid():
                form.save()
                return HttpResponseRedirect("/sicop/restrito/caixa/edicao/"+str(id)+"/")
    else:
        form = FormCaixa(instance=instance)
        
        
    # retornar o conteudo da caixa de acordo com o tipocaixa
    
#    processos = Tbprocessobase.objects.all().filter( tbcaixa__id = id )   

    p_rural = Tbprocessorural.objects.all().filter( tbprocessobase__tbcaixa__id = id )
    p_clausula = Tbprocessoclausula.objects.all().filter( tbprocessobase__tbcaixa__id = id )
    p_urbano = Tbprocessourbano.objects.all().filter( tbprocessobase__tbcaixa__id = id )
    processos = []
    for obj in p_rural:
        processos.append( obj )
    for obj in p_clausula:
        processos.append( obj )
    for obj in p_urbano:
        processos.append( obj )

    
    pecas = Tbpecastecnicas.objects.all().filter( tbcaixa__id = id )    
    conteudo = ""
    if len(processos) > 0:
        conteudo = str(len(processos))+" Processo(s)"
    if pecas.count() > 0:
        conteudo += str(pecas.count())+" Peca(s) Tecnica(s)"
        
    if len(processos) <= 0 and pecas.count() <= 0:
        conteudo = "Caixa Vazia"
    
    
    return render_to_response('sicop/restrito/caixa/edicao.html', {"form":form,'processos':processos,'pecas':pecas,'conteudo':conteudo,"tipocaixa":tipocaixa}, context_instance = RequestContext(request))


def relatorio_pdf(request):
    # montar objeto lista com os campos a mostrar no relatorio/pdf
    lista = request.session['relatorio_caixa']
    
    dados = []
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))
    for obj in lista:
        dados.append( Paragraph( obj.nmlocalarquivo , styles["Normal"]) )
        dados.append(Spacer(100,1))
        dados.append( Paragraph( obj.tbtipocaixa.nmtipocaixa , styles["Normal"]) )
        dados.append(Spacer(1,12))

    if lista:
        resp = relatorio_pdf_base_consulta(request, dados, 'RELATORIO DAS CAIXAS')
        return resp
    else:
        return HttpResponseRedirect("/sicop/restrito/caixa/consulta/")


def relatorio_ods(request):

    # montar objeto lista com os campos a mostrar no relatorio/pdf
    lista = request.session['relatorio_caixa']
    
    if lista:
        ods = ODS()
        sheet = relatorio_ods_base_header('Caixas','Relatorio Caixas', ods)
        
        # subtitle
        sheet.getCell(0, 1).setAlignHorizontal('center').stringValue( 'Nome' ).setFontSize('14pt')
        sheet.getCell(1, 1).setAlignHorizontal('center').stringValue( 'Tipo' ).setFontSize('14pt')
        sheet.getRow(1).setHeight('20pt')
        
    #TRECHO PERSONALIZADO DE CADA CONSULTA
        #DADOS
        x = 0
        for obj in lista:
            sheet.getCell(0, x+2).setAlignHorizontal('center').stringValue(obj.nmlocalarquivo)
            sheet.getCell(1, x+2).setAlignHorizontal('center').stringValue(obj.tbtipocaixa.nmtipocaixa)    
            x += 1
        
    #TRECHO PERSONALIZADO DE CADA CONSULTA     
       
        relatorio_ods_base(ods, 'caixas')
        # generating response
        response = HttpResponse(mimetype=ods.mimetype.toString())
        response['Content-Disposition'] = 'attachment; filename="relatorio-caixas.ods"'
        ods.save(response)
    
        return response
    else:
        return HttpResponseRedirect( "/sicop/restrito/caixa/consulta" )


def relatorio_csv(request):
    # montar objeto lista com os campos a mostrar no relatorio/pdf
    lista = request.session['relatorio_caixa']
    if lista:
        response = HttpResponse(content_type='text/csv')     
        writer = relatorio_csv_base(response, 'relatorio-caixas')
        writer.writerow(['Nome', 'Tipo'])
        for obj in lista:
            writer.writerow([obj.nmlocalarquivo, obj.tbtipocaixa.nmtipocaixa])
        return response
    else:
        return HttpResponseRedirect( '/sicop/restrito/caixa/consulta/' )

def validacao(request_form):
    warning = True
    if request_form.POST['nmlocalarquivo'] == '':
        messages.add_message(request_form,messages.WARNING,'Informe um nome para a caixa')
        warning = False
    return warning