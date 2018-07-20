import re
from os import path
import glob
import chardet

from .base import Base


class Source(Base):
    def __init__(self, vim):
        super().__init__(vim)
        self.name = 'latex-bib'
        self.filetypes = ['tex']
        self.input_pattern = r'(\\cite{|\\citep{|\\citet{)[^"#\'()={}%\\]*?'
        self.input_pattern_re = re.compile(
            r'(\\cite{|\\citep{|\\citet{)([^"#\'()={}%\\]*?,)*'
        )
        self.mark = '[bib]'
        self.cite_key_re = re.compile(r'{.+,')
        self.bibitem_re = re.compile(r'\\bibitem(?:\[\d+\])?\{(.+?)\}')
        self.bib_encs = {}

    def get_complete_position(self, context):
        if not self.input_pattern_re.search(context['input']):
            return -1

        # Find complete position; the match before and nearest to cursor.
        cursor_pos = self.vim.call('getcurpos')[2]
        match_pos = 0
        while 1:
            match = self.input_pattern_re.search(
                context['input'],
                match_pos
            )
            if match and match.end() < cursor_pos:
                match_pos = match.end()
            else:
                break
        return match_pos

    def gather_candidates(self, context):
        candidates = []

        # Find bib files that are contained in the same directory as
        # the TeX file.
        file_dir = self.vim.call('expand', '%:p:h')
        bib_files = glob.glob(path.join(file_dir, '*.bib'))

        # Search cite key within bib files
        # TODO: Make candidates `dict`, and add `abbr` key to show
        #       bib info.
        enc_detector = chardet.UniversalDetector()
        for bib in bib_files:
            # Detect encoding, assuming the encoding never changes
            if bib not in self.bib_encs.keys():
                enc_detector.reset()
                for l in open(bib, 'rb'):
                    enc_detector.feed(l)
                enc_detector.close()
                self.bib_encs[bib] = enc_detector.result['encoding']

            with open(bib, 'r', encoding=self.bib_encs[bib]) as f:
                bib_lines = f.readlines()
            for l in bib_lines:
                if l[0] == '@':
                    candidates.append(self.cite_key_re.search(l)[0][1:-1])

        # Search cite key defined by \bibitem within TeX files
        tex_files = glob.glob(path.join(file_dir, '*.tex'))
        for tex in tex_files:
            # Detect encoding, assuming the encoding never changes
            if tex not in self.bib_encs.keys():
                enc_detector.reset()
                for l in open(tex, 'rb'):
                    enc_detector.feed(l)
                enc_detector.close()
                self.bib_encs[tex] = enc_detector.result['encoding']

            with open(tex, 'r', encoding=self.bib_encs[tex]) as f:
                tex_lines = f.readlines()
            for l in tex_lines:
                match = self.bibitem_re.search(l)
                if match:
                    candidates.append(match[1])

        return candidates
