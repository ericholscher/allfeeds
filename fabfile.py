config.fab_user = 'eric'

def git_pull():
    "Updates the repository."
    run("cd ~/lib/$(repo)/; git pull $(parent) $(branch)")

def git_reset():
    "Resets the repository to specified version."
    run("cd ~/lib/$(repo)/; git reset --hard $(hash)")

def production():
    config.fab_hosts = ['fredvents.com']
    config.repos = (('allfeeds','origin','master'),)

def staging():
    config.fab_hosts = ['holscher.mine.nu']
    config.repos = (('allfeeds','origin','master'),)

def reboot():
    "Reboot Apache2 server."
    sudo("apache2ctl graceful")

def pull():
    require('fab_hosts', provided_by=[production])
    for repo, parent, branch in config.repos:
        config.repo = repo
        config.parent = parent
        config.branch = branch
        invoke(git_pull)

def reset(repo, hash):
    """
    Reset all git repositories to specified hash.
    Usage:
        fab reset:repo=my_repo,hash=etcetc123
    """
    require("fab_hosts", provided_by=[staging, production])
    config.hash = hash
    config.repo = repo
    invoke(git_reset)
