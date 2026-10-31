from .models import Treinador


def treinador_logado(request):
    """Disponibiliza o treinador do usuário logado para o menu lateral."""
    if request.user.is_authenticated:
        return {'treinador_logado': Treinador.objects.filter(usuario=request.user).first()}
    return {}
