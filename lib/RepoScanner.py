import git
import os

class RepoScanner():

    def __init__(self, repopath):
        self._root = repopath
        try:
            self._repo = git.Repo(self._root)
        except:
            # TODO: color log
            print('\033[44m\033[37m[INFO]\033[0m Fail to open git repo at: %s' % (repopath))
            while (True):
                in_content = input('\033[44m\033[37m[INFO]\033[0m Try to create a new repo? [y/n]: ')
                if (in_content == 'y' or in_content == 'Y'):
                    break
                if (in_content == 'n' or in_content == 'N'):
                    return
            try:
                self._repo = git.Repo.init(path=self._root)
            except Exception as e:
                raise e

    def getNewFiles(self):
        return self._repo.untracked_files

    def scan(self):
        diff = [ item.a_path for item in self._repo.index.diff(None) ]
        deleted = []
        changed = []
        for item in diff:
            if not os.path.exists(os.path.join(self._root, item)):
                deleted.append(item)
            else: changed.append(item)
        return {'new': self.getNewFiles(), 'deleted': deleted, 'changed': changed}
