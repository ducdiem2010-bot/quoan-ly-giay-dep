"""Kiểm thử JS localStorage trên Node, không chỉ tìm chuỗi văn bản."""
import shutil
import subprocess
import unittest
from pathlib import Path

JS = Path(__file__).resolve().parents[1] / 'app' / 'static' / 'js' / 'w13_recently_viewed.js'


@unittest.skipUnless(shutil.which('node'),'Node.js unavailable')
class RecentlyViewedTests(unittest.TestCase):
    def execute(self, previous, product_id):
        script=r'''
const vm = require('vm'),fs=require('fs');
const old=JSON.parse(process.argv[1]), viewed=process.argv[2];
const storage = new Map([['shoes_store_w13_recent_ids',JSON.stringify(old)]]);
const context = {
  localStorage:{getItem:(k)=>storage.get(k)||null,setItem:(k,v)=>storage.set(k,v)},
  document:{querySelector:(selector)=>selector==='[data-w13-view-product]'&&viewed!=='none'?{getAttribute:()=>viewed}:null},
  console:console
};
vm.runInNewContext(fs.readFileSync(process.argv[3],'utf8'),context);
process.stdout.write(storage.get('shoes_store_w13_recent_ids'));
'''
        import json
        cmd=['node','-e',script,json.dumps(previous),str(product_id),str(JS)]
        completed=subprocess.run(cmd,capture_output=True,text=True,check=True,timeout=10)
        return json.loads(completed.stdout)
    def test_most_recent_first_no_duplicates(self):
        self.assertEqual(self.execute([4,5,4],5),[5,4])
    def test_keep_eight(self):
        self.assertEqual(self.execute(list(range(1,11)),11),[11,1,2,3,4,5,6,7])
    def test_bad_id_ignored(self):
        self.assertEqual(self.execute([3],'-1'),[3])
    def test_no_personal_fields(self):
        self.assertEqual(self.execute([2],3),[3,2])

if __name__=='__main__':unittest.main()
