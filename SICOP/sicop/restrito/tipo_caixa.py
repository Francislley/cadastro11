from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext
from sicop.forms import FormTipoCaixa
from django.http import HttpResponseRedirect
from sicop.models import Tbtipocaixa
from django.contrib import messages

@login_required
def consulta(request):
    if request.method == "POST":
        nome = request.POST['nmtipocaixa']
        lista = Tbtipocaixa.objects.all().filter( nmtipocaixa__contains=nome )
    else:
        lista = Tbtipocaixa.objects.all()
    lista = lista.order_by( 'id' )
    return render_to_response('sicop/restrito/tipo_caixa/consulta.html' ,{'lista':lista}, context_instance = RequestContext(request))

    
@login_required
def cadastro(request):
    if request.method == "POST":
        form = FormTipoCaixa(request.POST)
        if validacao(request):
            if form.is_valid():
                form.save()
                return HttpResponseRedirect("/sicop/restrito/tipo_caixa/consulta/") 
    else:
        form = FormTipoCaixa()
    return render_to_response('sicop/restrito/tipo_caixa/cadastro.html',{"form":form}, context_instance = RequestContext(request))

@login_required
def edicao(request, id):
    instance = get_object_or_404(Tbtipocaixa, id=id)
    if request.method == "POST":
        form = FormTipoCaixa(request.POST,request.FILES,instance=instance)
        if validacao(request):
            if form.is_valid():
                form.save()
                return HttpResponseRedirect("/sicop/restrito/tipo_caixa/consulta/")
    else:
        form = FormTipoCaixa(instance=instance)
    return render_to_response('sicop/restrito/tipo_caixa/edicao.html', {"form":form}, context_instance = RequestContext(request))


def validacao(request_form):
    warning = True
    if request_form.POST['nmtipocaixa'] == '':
        messages.add_message(request_form,messages.WARNING,'Informe um nome para o tipo caixa')
        warning = False
    return warning