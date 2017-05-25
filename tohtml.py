"""
Render all tracks from the input into html page.
"""

import sys
import os

import track


def write_report(tracks):
    os.makedirs('report', exist_ok=True)
    with open('report/index.html', 'w') as report:
        report.write('<!doctype html>\n')
        report.write('<body>\n')
        report.write('<table>\n')
        report.write('''<tr>
<th>descr<th>S<th>T<th>U<th>D<th>P<th>image
</tr>\n''')
        for i, t in enumerate(tracks, start=1):
            report.write('<tr><td>%s</td>' % t.path)
            report.write('<td>{S}</td><td>{T}</td><td>{U}</td><td>{D}</td><td>{P}</td>'.format(
                S=t.path.count('S'),
                T=t.path.count('R') + t.path.count('L'),
                U=t.path.count('U'),
                D=t.path.count('D'),
                P=t.count_pillars(),
            ))
            report.write('<td><img src="preview%02d.png"></td>' % i)
            report.write('</tr>\n')
            t.draw('report/preview%002d.png' % i)
        report.write('</table></body>\n')


def main():
    tracks = []
    for line in sys.stdin:
        path = line.strip()
        tracks.append(track.Track(path))
    write_report(tracks)


if __name__ == '__main__':
    main()
