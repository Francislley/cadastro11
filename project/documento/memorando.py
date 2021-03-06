from django.contrib.auth.decorators import login_required, permission_required,\
    user_passes_test
from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext
from django.http import HttpResponseRedirect
from project.tramitacao.models import AuthUser
from project.documento.models import Memorando
from django.contrib import messages
from project.tramitacao.admin import verificar_permissao_grupo
from django.http.response import HttpResponse

from odslib import ODS
import datetime
from project.core.funcoes import format_datetime, gerar_pdf,mes_do_ano_texto
from os.path import abspath, join, dirname
from project import settings
from django.db.models import Q

@permission_required('documento.memorando_consulta', login_url='/excecoes/permissao_negada/', raise_exception=True)
def consulta(request):
    lista = []
    if request.method == "POST":
        numero = request.POST['numero']
        if request.POST['numero'] != '':
            lista = Memorando.objects.filter( numero__icontains=numero)
            lista = lista.order_by( '-data_documento' )
        texto = request.POST['texto']
        if texto != '':
            lista = Memorando.objects.filter(
                Q( assunto__icontains=texto )|
                Q( mensagem__icontains=texto )|
                Q( remetente__icontains=texto )|
                Q( destinatario__icontains=texto )|
                Q( localidade__icontains=texto )|
                Q( signatario__icontains=texto )|                
                Q( cargo_signatario__icontains=texto )|
                Q( data_documento__icontains=texto )
            )
            lista = lista.order_by( '-data_documento' )

    return render_to_response('documento/memorando/consulta.html' ,{'lista':lista}, context_instance = RequestContext(request))
    
@permission_required('documento.memorando_cadastro', login_url='/excecoes/permissao_negada/', raise_exception=True)
def cadastro(request):
    if request.method == "POST":
        f_obj = Memorando(
            numero = request.POST['numero'],
            mensagem = request.POST['mensagem'],
            auth_user = AuthUser.objects.get( pk = request.user.id ),
            localidade = request.POST['localidade'],
            assunto = request.POST['assunto'],
            remetente = request.POST['remetente'],
            destinatario = request.POST['destinatario'],
            signatario = request.POST['signatario'].upper(),
            cargo_signatario = request.POST['cargo_signatario'].title(),
            data_cadastro = datetime.datetime.now(),
            circular = request.POST.get('circular',False)
        )        
        dt = request.POST['data_documento'].split('/')
        f_obj.data_documento = datetime.datetime(day=int(dt[0]),month=int(dt[1]),year=int(dt[2]))
        f_obj.save()
        
        dados = {
            'brasao':abspath(join(dirname(__file__), '../../staticfiles'))+'/img/slide_1.jpg',
            'numero':f_obj.numero,
            'assunto':f_obj.assunto,
            'mensagem':f_obj.mensagem,
            'remetente':f_obj.remetente,
            'destinatario':f_obj.destinatario,
            'localidade':f_obj.localidade,
            'dia':dt[0],
            'mes':mes_do_ano_texto(int(dt[1])),
            'ano':dt[2],
            'signatario':f_obj.signatario,
            'cargo_signatario':f_obj.cargo_signatario,
            'circular':f_obj.circular
        }
        return gerar_pdf(request,'/documento/memorando/memorando.html',dados, settings.MEDIA_ROOT+'/tmp','memorando.pdf')

    return render_to_response('documento/memorando/cadastro.html',{'data_hoje':format_datetime(datetime.datetime.now()).replace('/','')}, context_instance = RequestContext(request))

@permission_required('documento.memorando_consulta', login_url='/excecoes/permissao_negada/', raise_exception=True)
def edicao(request, id):
    instance = get_object_or_404(Memorando, id=id)
    if request.method == "POST":

        if not request.user.has_perm('documento.memorando_edicao'):
            return HttpResponseRedirect('/excecoes/permissao_negada/') 

        f_obj = Memorando(
            id = instance.id,
            numero = request.POST['numero'],
            mensagem = request.POST['mensagem'],
            auth_user = AuthUser.objects.get( pk = request.user.id ),
            localidade = request.POST['localidade'],
            assunto = request.POST['assunto'],
            remetente = request.POST['remetente'],
            destinatario = request.POST['destinatario'],
            signatario = request.POST['signatario'].upper(),
            cargo_signatario = request.POST['cargo_signatario'].title(),
            data_cadastro = instance.data_cadastro,
            circular = request.POST.get('circular',False)
        )

        dt = request.POST['data_documento'].split('/')
        f_obj.data_documento = datetime.datetime(day=int(dt[0]),month=int(dt[1]),year=int(dt[2]))

        f_obj.save()
        #return HttpResponseRedirect("/documento/memorando/edicao/"+str(id)+"/")
        dados = {
            'brasao':abspath(join(dirname(__file__), '../../staticfiles'))+'/img/slide_1.jpg',
            'numero':f_obj.numero,
            'assunto':f_obj.assunto,
            'mensagem':f_obj.mensagem,
            'remetente':f_obj.remetente,
            'destinatario':f_obj.destinatario,
            'localidade':f_obj.localidade,
            'dia':dt[0],
            'mes':mes_do_ano_texto(int(dt[1])),
            'ano':dt[2],
            'signatario':f_obj.signatario,
            'cargo_signatario':f_obj.cargo_signatario,
            'circular':f_obj.circular        
        }
        return gerar_pdf(request,'/documento/memorando/memorando.html',dados, settings.MEDIA_ROOT+'/tmp','memorando.pdf')

    return render_to_response('documento/memorando/edicao.html', {"memorando":instance}, context_instance = RequestContext(request))
