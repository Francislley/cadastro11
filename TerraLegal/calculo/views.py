from django.contrib.auth.decorators import permission_required
from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext
from TerraLegal.calculo.models import Tbextrato
from TerraLegal.tramitacao.models import Tbmunicipio
from decimal import Decimal
from datetime import date
from TerraLegal.tramitacao.restrito.processo import formatDataToText

nome_relatorio      = "relatorio_portaria80"
response_consulta  = "/sicop/restrito/portaria80/calculo/"
titulo_relatorio    = "Calculo Portaria 80 - Clausulas Resolutivas"

@permission_required('sicop.titulo_calculo_portaria23', login_url='/excecoes/permissao_negada/', raise_exception=True)
def consulta(request):
    p_extrato = []
    if request.method == "POST":
        numero = request.POST['numero'].replace('.','').replace('/','').replace('-','')
        cpf = request.POST['cpf'].replace('.','').replace('/','').replace('-','')
        requerente = request.POST['requerente']
        titulo = request.POST['cdtitulo']
        p_extrato = []
        p_extrato = Tbextrato.objects.all().filter(numero_processo__icontains = numero,cpf_req__icontains = cpf,
                                nome_req__icontains = requerente, id_req__icontains = titulo,  situacao_processo__icontains = 'Titulado')
        
    '''gravando na sessao o resultado da consulta preparando para o relatorio/pdf'''
    return render_to_response('portaria23/consulta.html',{'lista':p_extrato}, context_instance = RequestContext(request))

@permission_required('sicop.titulo_calculo_portaria23', login_url='/excecoes/permissao_negada/', raise_exception=True)
def emissao(request,id):
    instance = get_object_or_404(Tbextrato, id=id)
    municipio = Tbmunicipio.objects.all()
    hoje = date.today()
    prestacao = (float(instance.valor_imovel)/17.0)
    vencimento = instance.data_vencimento_primeira_prestacao
    titulado = vencimento.replace(vencimento.year - 3)
    '''calculo do indice de correcao / encargos depende do valor e tamanho da area'''
    area = instance.area_medida
    modulos = instance.tamanho_modulos_fiscais
    valor_imovel = instance.valor_imovel.quantize(Decimal('1.00'))
    
    if modulos > 4:
        indice = 6.75/100
    else:
        if valor_imovel <= 40000:
            indice = 1.0/100
        else: 
            if valor_imovel > 40000 and valor_imovel <= 100000:
                indice = 2.0/100
            else: 
                if valor_imovel > 100000:
                    indice = 4.0/100

    desconto = 0
    NossaEscola = False
    if request.method == "POST":
        if request.POST.get('stNossaEscola',False):
            desconto_1 = float(prestacao) / 2
            #desconto = "{0:.2f}".format(desconto) 
            #prestacao_com_desconto = "{0:.2f}".format(prestacao_com_desconto)
            desconto = desconto + desconto_1
            NossaEscola = True

    
    '''se ainda nao tiver vencido ha incidencia de  correcao'''
    
    prestacao_com_desconto = prestacao - desconto
    dias_correcao = hoje - titulado  
    correcao = float(prestacao_com_desconto)*((float(dias_correcao.days)/360.) * indice)
    principal_corrigido = float(prestacao_com_desconto) + correcao
   
    '''caso tenha vencido, incide juros de 1% ao mes sobre o valor corrigido'''
    juros = 0 
    if hoje > vencimento:
        dias_juros = hoje - vencimento
        juros = ((float(dias_juros.days)+1)/30)* (1.0/100.0) * principal_corrigido  
        #principal_corrigido_juros = (juros + principal_corrigido)
        #juros = "{0:.2f}".format(juros)
    principal_corrigido_juros = principal_corrigido + juros

    #principal_corrigido = principal_corrigido.quantize(Decimal('1,00'))    
    
    
    prestacao = "{0:.2f}".format(prestacao)
    titulado = formatDataToText(titulado)
    vencimento = formatDataToText(vencimento)
    correcao = "{0:.2f}".format(correcao)
    principal_corrigido_juros = "{0:.2f}".format(principal_corrigido_juros)
    desconto = "{0:.2f}".format(desconto)
    juros = "{0:.2f}".format(juros)

    ordem = 1
    indice = indice * 100
    
    return render_to_response('portaria23/calculo.html' ,locals(), context_instance = RequestContext(request))


@permission_required('sicop.titulo_calculo_portaria23', login_url='/excecoes/permissao_negada/', raise_exception=True)
def digitar(request):
        
    return render_to_response('portaria23/calculo.html' ,locals(), context_instance = RequestContext(request))
