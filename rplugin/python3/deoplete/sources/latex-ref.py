import re
from os import path
import glob
import chardet

from .base import Base


class Source(Base):
    def __init__(self, vim):
        super().__init__(vim)
        self.name = 'latex-ref'
        self.filetypes = ['tex']
        self.input_pattern = r'(\\ref{|\\cref{)[^"#\'()={}%\\]*?'
        self.input_pattern_re = re.compile(
            r'(\\ref{|\\cref{)([^"#\'()={}%\\]*?,)*'
        )
        self.mark = '[ref]'
        self.ref_re = re.compile(r'\\label{.+?}')
        self.tex_encs = {}

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

        # Find TeX files that are contained in the same directory as
        # current file.
        file_dir = self.vim.call('expand', '%:p:h')
        tex_files = glob.glob(path.join(file_dir, '*.tex'))

        # Search labels within TeX files
        enc_detector = chardet.UniversalDetector()
        for tex in tex_files:
            # Detect encoding, assuming the encoding never changes
            if tex not in self.tex_encs.keys():
                enc_detector.reset()
                for l in open(tex, 'rb'):
                    enc_detector.feed(l)
                enc_detector.close()
                self.tex_encs[tex] = enc_detector.result['encoding']

            with open(tex, 'r', encoding=self.tex_encs[tex]) as f:
                tex_str = f.read()
            for match in self.ref_re.findall(tex_str):
                candidates.append(match[7:-1])

        return candidates
