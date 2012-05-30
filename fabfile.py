import sys
sys.path.append('../')
from fabric.api import task, sudo, run
from fabric.state import env
from gitric.api import git_seed, git_reset, allow_dirty, force_push

env.hosts = ['localhost']

@task
def prod():
    '''an example production deployment'''
    #env.user = 'test-deployer'
    #env.hosts = ['m242', 'm243']

@task
def deploy(commit=None):
    '''an example deploy action'''
    repo_path = '/home/snaplabs.com/deploy/notewave'

    run("mkdir -p %s" % repo_path)
    # force_push()
    git_seed(repo_path, commit)
    # stop your service here
    git_reset(repo_path, commit)
    sudo("cp %s/conf/nginx_notewave.conf /etc/nginx/vhosts/" % repo_path)
    sudo("cp %s/conf/supervisor_notewave.conf /etc/supervisor.d/" % repo_path)
    sudo("supervisorctl restart notewave:*")
    # restart your service here
