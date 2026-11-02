package org.polaris.ocrbench;
import android.app.Activity;import android.os.Bundle;import android.graphics.Bitmap;import android.graphics.BitmapFactory;import android.widget.TextView;
import com.google.android.gms.tasks.Tasks;import com.google.mlkit.vision.common.InputImage;import com.google.mlkit.vision.text.*;
import com.google.mlkit.vision.text.latin.TextRecognizerOptions;import com.google.mlkit.vision.text.japanese.JapaneseTextRecognizerOptions;import com.google.mlkit.vision.text.chinese.ChineseTextRecognizerOptions;import com.google.mlkit.vision.text.korean.KoreanTextRecognizerOptions;
import org.json.*;import java.io.*;import java.util.concurrent.*;
public class MainActivity extends Activity {
 public void onCreate(Bundle b){super.onCreate(b);TextView v=new TextView(this);v.setText("Running actual ML Kit OCR; results in app files");setContentView(v);Executors.newSingleThreadExecutor().execute(()->runBench());}
 private void save(JSONArray results)throws Exception{try(FileWriter w=new FileWriter(new File(getFilesDir(),"results.json"))){w.write(results.toString(2));}}
 private void runBench(){JSONArray results=new JSONArray();try{
  String config;try(InputStream s=getAssets().open("cases/cases.json")){ByteArrayOutputStream bytes=new ByteArrayOutputStream();byte[] buffer=new byte[8192];int n;while((n=s.read(buffer))!=-1)bytes.write(buffer,0,n);config=bytes.toString("UTF-8");}JSONArray cases=new JSONArray(config);
  for(int i=0;i<cases.length();i++){JSONObject c=cases.getJSONObject(i),out=new JSONObject();out.put("id",c.getString("id"));long begin=System.nanoTime();TextRecognizer rec=null;Bitmap bitmap=null;
   try{String lang=c.getString("lang");if(lang.equals("ja"))rec=TextRecognition.getClient(new JapaneseTextRecognizerOptions.Builder().build());else if(lang.startsWith("zh"))rec=TextRecognition.getClient(new ChineseTextRecognizerOptions.Builder().build());else if(lang.equals("ko"))rec=TextRecognition.getClient(new KoreanTextRecognizerOptions.Builder().build());else rec=TextRecognition.getClient(TextRecognizerOptions.DEFAULT_OPTIONS);
    try(InputStream in=getAssets().open("cases/"+c.getString("file"))){bitmap=BitmapFactory.decodeStream(in);}Text text=Tasks.await(rec.process(InputImage.fromBitmap(bitmap,0)),180,TimeUnit.SECONDS);
    out.put("text",text.getText());JSONArray lines=new JSONArray();for(Text.TextBlock block:text.getTextBlocks())for(Text.Line line:block.getLines()){JSONObject l=new JSONObject();l.put("text",line.getText());if(line.getBoundingBox()!=null){l.put("x",line.getBoundingBox().left);l.put("y",line.getBoundingBox().top);l.put("width",line.getBoundingBox().width());l.put("height",line.getBoundingBox().height());}lines.put(l);}out.put("lines",lines);out.put("status","OK");
    if(c.getString("id").equals("en-long-full")){
     JSONObject strips=new JSONObject();strips.put("id","en-long-strips");JSONArray merged=new JSONArray();long stripBegin=System.nanoTime();int top=0,region=0;
     while(true){int bottom=Math.min(top+2048,bitmap.getHeight());Bitmap tile=Bitmap.createBitmap(bitmap,0,top,bitmap.getWidth(),bottom-top);Text recognized=Tasks.await(rec.process(InputImage.fromBitmap(tile,0)),180,TimeUnit.SECONDS);
      for(Text.TextBlock b2:recognized.getTextBlocks())for(Text.Line l2:b2.getLines())if(l2.getBoundingBox()!=null){android.graphics.Rect r=l2.getBoundingBox();JSONObject l=new JSONObject();l.put("text",l2.getText());l.put("x",r.left);l.put("y",r.top+top);l.put("width",r.width());l.put("height",r.height());l.put("region",region);l.put("edge",Math.max(0,Math.min(r.top,bottom-top-r.bottom)));merged.put(l);}
      tile.recycle();region++;if(bottom==bitmap.getHeight())break;top=bottom-384;
     }
     strips.put("lines",merged);strips.put("regions",region);strips.put("status","OK");strips.put("elapsed_ms",(System.nanoTime()-stripBegin)/1000000);strips.put("text","Raw overlapping lines; deduplicate geometrically on host");results.put(strips);save(results);
    }

   }catch(Throwable e){out.put("status","ERROR");out.put("error",e.getClass().getSimpleName()+": "+e.getMessage());}
   finally{if(rec!=null)rec.close();if(bitmap!=null)bitmap.recycle();}
   out.put("elapsed_ms",(System.nanoTime()-begin)/1000000);results.put(out);save(results);
  }
  try(FileWriter w=new FileWriter(new File(getFilesDir(),"done.txt"))){w.write("done");}
 }catch(Throwable e){try(FileWriter w=new FileWriter(new File(getFilesDir(),"fatal.txt"))){w.write(e.toString());}catch(Exception ignored){}}}
}
