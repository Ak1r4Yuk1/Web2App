import os
import sys
import shutil
import subprocess
import textwrap
import random
import string
import platform
from PIL import Image
# QUESTO SCRIPT È IL RISULTATO FINALE E FUNZIONANTE.
# È MULTIPIATTAFORMA (WINDOWS/LINUX/MAC).
# ESECUZIONE: python3 crea_app_finale.py <nome_cartella_web>

# --- CONTENUTO DEI FILE TEMPLATE ---

def get_settings_gradle():
    return "include ':app'\n"

def get_root_build_gradle():
    return textwrap.dedent("""
    buildscript {
        repositories {
            google()
            mavenCentral()
        }
        dependencies {
            classpath 'com.android.tools.build:gradle:8.2.2'
        }
    }

    allprojects {
        repositories {
            google()
            mavenCentral()
        }
    }
    """)

def get_app_build_gradle(package_name):
    return textwrap.dedent(f"""\
    import java.util.Properties
    import java.io.FileInputStream

    def keystorePropertiesFile = file("keystore.properties")
    def keystoreProperties = new Properties()
    if (keystorePropertiesFile.exists()) {{
        keystoreProperties.load(new FileInputStream(keystorePropertiesFile))
    }}

    apply plugin: 'com.android.application'

    android {{
        namespace '{package_name}'
        compileSdkVersion 33
        
        signingConfigs {{
            release {{
                if (keystorePropertiesFile.exists()) {{
                    storeFile file(keystoreProperties['storeFile'])
                    storePassword keystoreProperties['storePassword']
                    keyAlias keystoreProperties['keyAlias']
                    keyPassword keystoreProperties['keyPassword']
                }}
            }}
        }}

        defaultConfig {{
            applicationId "{package_name}"
            minSdkVersion 21
            targetSdkVersion 33
            versionCode 1
            versionName "1.0"
        }}
        
        buildTypes {{
            release {{
                minifyEnabled false
                proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
                signingConfig signingConfigs.release
            }}
        }}
    }}

    dependencies {{
        // No external dependencies needed for a simple WebView
    }}
    """)

def get_android_manifest(package_name, app_name):
    return f'''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">

    <uses-permission android:name="android.permission.INTERNET" />

    <application
        android:allowBackup="true"
        android:label="{app_name}"
        android:icon="@mipmap/ic_launcher"
        android:roundIcon="@mipmap/ic_launcher"
        android:supportsRtl="true"
        android:theme="@android:style/Theme.NoTitleBar"
        android:usesCleartextTraffic="true">
        <activity android:name=".MainActivity"
                  android:exported="true"
                  android:configChanges="orientation|screenSize">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
'''

def get_android_manifest_tv(package_name, app_name):
    # Nota l'aggiunta di android:banner, le uses-feature e la category LEANBACK_LAUNCHER
    return f'''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">

    <uses-permission android:name="android.permission.INTERNET" />
    
    <uses-feature android:name="android.hardware.touchscreen" android:required="false" />
    <uses-feature android:name="android.software.leanback" android:required="false" />

    <application
        android:allowBackup="true"
        android:label="{app_name}"
        android:icon="@mipmap/ic_launcher"
        android:roundIcon="@mipmap/ic_launcher"
        android:banner="@drawable/tv_banner"
        android:supportsRtl="true"
        android:theme="@android:style/Theme.NoTitleBar"
        android:usesCleartextTraffic="true">
        
        <activity android:name=".MainActivity"
                  android:exported="true"
                  android:configChanges="orientation|screenSize">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LEANBACK_LAUNCHER" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
'''

def generate_tv_banner(source_icon, custom_banner_path, res_path):
    # Genera il banner TV.
    # Priorità: 1. Immagine banner personalizzata fornita dall'utente
    #           2. Generazione automatica partendo dall'icona app
    #           3. Generazione generica (colore solido)
    
    drawable_dir = os.path.join(res_path, "drawable")
    os.makedirs(drawable_dir, exist_ok=True)
    banner_dest_path = os.path.join(drawable_dir, "tv_banner.png")

    try:
        # CASO 1: L'utente ha fornito un'immagine specifica per il banner
        if custom_banner_path and os.path.exists(custom_banner_path):
            img = Image.open(custom_banner_path).convert("RGBA")
            # Ridimensiona forzatamente a 320x180 (o mantieni aspect ratio crop)
            # Qui facciamo un resize semplice per sicurezza
            img = img.resize((320, 180), Image.LANCZOS)
            img.save(banner_dest_path, format="PNG")
            print(f"   - Banner TV personalizzato applicato: {custom_banner_path}")
            return

        # CASO 2: Nessun banner fornito, usiamo l'icona dell'app
        if source_icon and os.path.exists(source_icon):
            print("   ⚠️  Banner TV non specificato: ne verrà generato uno usando l'icona dell'app.")
            img = Image.open(source_icon).convert("RGBA")
            # Sfondo grigio scuro elegante
            banner = Image.new('RGBA', (320, 180), (33, 33, 33, 255))
            # Icona ridimensionata per stare al centro
            img.thumbnail((140, 140), Image.LANCZOS)
            offset = ((320 - img.width) // 2, (180 - img.height) // 2)
            banner.paste(img, offset, img)
            banner.save(banner_dest_path, format="PNG")
            print(f"   - Banner TV generato automaticamente in {banner_dest_path}")
        
        # CASO 3: Nessuna immagine fornita affatto
        else:
            print("   ⚠️  Nessuna immagine fornita. Verrà creato un banner generico.")
            banner = Image.new('RGB', (320, 180), (70, 130, 180)) # Blu default
            banner.save(banner_dest_path, format="PNG")

    except Exception as e:
        print(f"❌ ERRORE generazione banner TV: {e}")

def get_main_activity(package_name):
    return textwrap.dedent(f"""
    package {package_name};

    import android.app.Activity;
    import android.os.Bundle;
    import android.webkit.WebSettings;
    import android.webkit.WebView;
    import android.webkit.WebViewClient;
    import android.webkit.WebChromeClient;
    import android.view.KeyEvent;
    import android.view.View;
    import android.view.ViewGroup;
    import android.view.WindowManager;
    import android.widget.FrameLayout;

    public class MainActivity extends Activity {{

        private WebView myWebView;
        private View mCustomView;
        private WebChromeClient.CustomViewCallback mCustomViewCallback;
        private FrameLayout mFullscreenContainer;

        @Override
        protected void onCreate(Bundle savedInstanceState) {{
            super.onCreate(savedInstanceState);
            setContentView(R.layout.activity_main);

            myWebView = (WebView) findViewById(R.id.webview);

            WebSettings webSettings = myWebView.getSettings();
            webSettings.setJavaScriptEnabled(true);
            webSettings.setDomStorageEnabled(true);
            webSettings.setAllowFileAccess(true);
            webSettings.setAllowContentAccess(true);
            webSettings.setMediaPlaybackRequiresUserGesture(false);

            myWebView.setWebViewClient(new WebViewClient());
            
            myWebView.setWebChromeClient(new WebChromeClient() {{
                @Override
                public void onShowCustomView(View view, CustomViewCallback callback) {{
                    if (mCustomView != null) {{
                        onHideCustomView();
                        return;
                    }}
                    mCustomView = view;
                    mCustomViewCallback = callback;

                    // 1. Attiva la modalità immersiva (Nasconde tasti Android e Status Bar)
                    getWindow().getDecorView().setSystemUiVisibility(
                            View.SYSTEM_UI_FLAG_LAYOUT_STABLE
                            | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
                            | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
                            | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                            | View.SYSTEM_UI_FLAG_FULLSCREEN
                            | View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY);

                    // 2. Prepara il container per il video
                    ViewGroup rootView = (ViewGroup) getWindow().getDecorView();
                    mFullscreenContainer = new FrameLayout(MainActivity.this);
                    mFullscreenContainer.setBackgroundColor(0xFF000000); // Nero assoluto
                    
                    mFullscreenContainer.addView(view, new FrameLayout.LayoutParams(
                            ViewGroup.LayoutParams.MATCH_PARENT,
                            ViewGroup.LayoutParams.MATCH_PARENT));
                    
                    rootView.addView(mFullscreenContainer, new ViewGroup.LayoutParams(
                            ViewGroup.LayoutParams.MATCH_PARENT,
                            ViewGroup.LayoutParams.MATCH_PARENT));

                    myWebView.setVisibility(View.GONE);
                }}

                @Override
                public void onHideCustomView() {{
                    if (mCustomView == null) return;

                    // 1. Ripristina la visibilità dell'interfaccia Android normale
                    getWindow().getDecorView().setSystemUiVisibility(View.SYSTEM_UI_FLAG_VISIBLE);

                    // 2. Rimuovi il video dal root layout
                    ViewGroup rootView = (ViewGroup) getWindow().getDecorView();
                    rootView.removeView(mFullscreenContainer);
                    mFullscreenContainer = null;
                    mCustomView = null;
                    mCustomViewCallback.onCustomViewHidden();
                    
                    // 3. Torna alla WebView
                    myWebView.setVisibility(View.VISIBLE);
                }}
            }});

            myWebView.loadUrl("file:///android_asset/index.html");
        }}

        @Override
        public boolean onKeyDown(int keyCode, KeyEvent event) {{
            // Se premo "Indietro" mentre il video è aperto, lo chiude
            if (keyCode == KeyEvent.KEYCODE_BACK && mCustomView != null) {{
                myWebView.getWebChromeClient().onHideCustomView();
                return true;
            }}
            // Altrimenti gestisce la cronologia della WebView
            if ((keyCode == KeyEvent.KEYCODE_BACK) && myWebView.canGoBack()) {{
                myWebView.goBack();
                return true;
            }}
            return super.onKeyDown(keyCode, event);
        }}
    }}
    """)
    
def get_layout(package_name):
    return f'''<?xml version="1.0" encoding="utf-8"?>
<RelativeLayout xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:tools="http://schemas.android.com/tools"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    tools:context="{package_name}.MainActivity">

    <WebView
        android:id="@+id/webview"
        android:layout_width="match_parent"
        android:layout_height="match_parent" />

</RelativeLayout>
'''

# ==============================
# ICON GENERATOR
# ==============================

def generate_icons(source_icon, res_path):
    sizes = {
        "mipmap-mdpi": 48,
        "mipmap-hdpi": 72,
        "mipmap-xhdpi": 96,
        "mipmap-xxhdpi": 144,
        "mipmap-xxxhdpi": 192
    }

    try:
        img = Image.open(source_icon).convert("RGBA")

        for folder, size in sizes.items():
            out_dir = os.path.join(res_path, folder)
            os.makedirs(out_dir, exist_ok=True)
            out_img = img.resize((size, size), Image.LANCZOS)
            out_img.save(os.path.join(out_dir, "ic_launcher.png"), format="PNG")
        print(f"   - Icone generate da {source_icon}")
    except Exception as e:
        print(f"❌ ERRORE durante la generazione delle icone: {e}")
        print("   Verranno utilizzate icone di default (se disponibili)")
def get_gradle_wrapper_properties():
    return "distributionUrl=https://services.gradle.org/distributions/gradle-8.5-bin.zip\n"

def get_local_properties(sdk_path):
    # Usa forward slashes anche su Windows, Java lo gestisce correttamente
    return f"sdk.dir={sdk_path.replace('\\', '/')}\n"

def get_gradlew_unix_script():
    return "#!/usr/bin/env sh\nset -e\nDIR=$(cd \"$(dirname \"$0\")\" && pwd)\nexec java -cp \"$DIR/gradle/wrapper/gradle-wrapper.jar\" org.gradle.wrapper.GradleWrapperMain \"$@\"\n"

def get_gradlew_windows_script():
    return textwrap.dedent("""
    @if "%DEBUG%" == "" @echo off
    @rem ##########################################################################
    @rem
    @rem  Gradle startup script for Windows
    @rem
    @rem ##########################################################################
    @rem Set local scope for the variables with windows NT shell
    if "%OS%"=="Windows_NT" setlocal
    set DIRNAME=%~dp0
    if "%DIRNAME%" == "" set DIRNAME=.
    set APP_BASE_NAME=%~n0
    set APP_HOME=%DIRNAME%
    @rem Add default JVM options here. You can also use JAVA_OPTS and GRADLE_OPTS to pass JVM options to this script.
    set DEFAULT_JVM_OPTS="-Xmx64m" "-Xms64m"
    @rem Find java.exe
    if defined JAVA_HOME goto findJavaFromJavaHome
    set JAVA_EXE=java.exe
    %JAVA_EXE% -version >NUL 2>&1
    if "%ERRORLEVEL%" == "0" goto init
    echo.
    echo ERROR: JAVA_HOME is not set and no 'java' command could be found in your PATH.
    echo.
    echo Please set the JAVA_HOME variable in your environment to match the
    echo location of your Java installation.
    echo.
    goto end
    :findJavaFromJavaHome
    set JAVA_HOME=%JAVA_HOME:"=%
    set JAVA_EXE=%JAVA_HOME%\\bin\\java.exe
    if exist "%JAVA_EXE%" goto init
    echo.
    echo ERROR: JAVA_HOME is set to an invalid directory: %JAVA_HOME%
    echo.
    echo Please set the JAVA_HOME variable in your environment to match the
    echo location of your Java installation.
    echo.
    goto end
    :init
    @rem Get command-line arguments, handling Windowz variants
    if not "%OS%" == "Windows_NT" goto win9xME_args
    if "%@eval[2+2]" == "4" goto 4NT_args
    :win9xME_args
    @rem Slurp the command line arguments.
    set CMD_LINE_ARGS=
    set _SKIP=2
    :win9xME_args_slurp
    if "x%~1" == "x" goto execute
    set CMD_LINE_ARGS=%*
    goto execute
    :4NT_args
    @rem Get arguments from the 4NT Shell.
    set CMD_LINE_ARGS=%*
    :execute
    @rem Setup the command line
    set CLASSPATH=%APP_HOME%\\gradle\\wrapper\\gradle-wrapper.jar
    @rem Execute Gradle
    "%JAVA_EXE%" %DEFAULT_JVM_OPTS% %JAVA_OPTS% %GRADLE_OPTS% "-Dorg.gradle.appname=%APP_BASE_NAME%" -classpath "%CLASSPATH%" org.gradle.wrapper.GradleWrapperMain %CMD_LINE_ARGS%
    :end
    if "%OS%"=="Windows_NT" endlocal
    :omega
    """)
# --- FUNZIONI DELLO SCRIPT ---

def print_usage():
    print("Uso: python3 crea_app.py <nome_cartella_web> [percorso_icona]")
    print("Esempio 1: python3 crea_app.py miosito")
    print("Esempio 2: python3 crea_app.py miosito ./logo.png")
    print("\nNote:")
    print("- La cartella web deve contenere un file index.html")
    print("- L'icona può essere in formato PNG, JPG, SVG, etc.")
    print("- Se non viene fornita un'icona, l'app userà l'icona di default")

# ==============================
# MAIN SCRIPT
# ==============================

def main():
    is_windows = platform.system() == "Windows"

    # Help rapido
    if len(sys.argv) < 2:
        print("\nUso: python3 crea_app.py <cartella_web> [opzioni]")
        print("\nOpzioni (in qualsiasi ordine):")
        print("  <percorso_icona.png>   : Imposta l'icona dell'app")
        print("  tv                     : Attiva modalità Android TV")
        print("  <percorso_banner.png>  : (Solo per TV) Imposta il banner specifico")
        print("\nEsempi:")
        print("  Solo Mobile : python3 crea_app.py miosito icona.png")
        print("  Solo TV     : python3 crea_app.py miosito icona.png tv banner.png")
        print("  TV (Auto)   : python3 crea_app.py miosito icona.png tv")
        sys.exit(1)

    web_dir_name = sys.argv[1].rstrip('/\\')
    if not os.path.isdir(web_dir_name):
        print(f"❌ Errore: La cartella '{web_dir_name}' non esiste.")
        sys.exit(1)

    # --- PARSING DEGLI ARGOMENTI AVANZATO ---
    icon_path = None
    banner_path = None
    target_mode = "mobile" # default

    # Analizziamo gli argomenti dal secondo in poi
    remaining_args = sys.argv[2:]
    
    # 1. Cerchiamo prima la modalità
    if "tv" in [arg.lower() for arg in remaining_args]:
        target_mode = "tv"
    
    # 2. Cerchiamo le immagini
    # La prima immagine trovata è SEMPRE l'icona.
    # La seconda immagine trovata (se siamo in TV) è il banner.
    found_images = []
    for arg in remaining_args:
        if arg.lower() in ["tv", "mobile"]:
            continue # Salta le parole chiave
        if os.path.exists(arg):
            found_images.append(arg)
    
    if len(found_images) > 0:
        icon_path = found_images[0]
    if len(found_images) > 1 and target_mode == "tv":
        banner_path = found_images[1]

    # --- FINE PARSING ---

    android_sdk_home = os.environ.get("ANDROID_HOME")
    if not android_sdk_home:
        print("❌ ERRORE: Variabile ANDROID_HOME non impostata.")
        sys.exit(1)
        
    java_home = os.environ.get("JAVA_HOME")
    if not java_home:
        print("❌ ERRORE: Variabile JAVA_HOME non impostata.")
        sys.exit(1)

    app_name = os.path.basename(os.path.abspath(web_dir_name))
    package_name = f"com.{app_name.lower().replace(' ', '').replace('-', '_')}"
    project_suffix = "_tv" if target_mode == "tv" else ""
    project_dir = f"{app_name}_android_app{project_suffix}"

    print(f"\n🚀 CONFIGURAZIONE RILEVATA:")
    print(f"   - App Name : {app_name}")
    print(f"   - Modalità : {target_mode.upper()}")
    print(f"   - Icona    : {icon_path if icon_path else 'Default Android'}")
    if target_mode == "tv":
        print(f"   - Banner   : {banner_path if banner_path else 'Automatico (da Icona)'}")

    # 1. Pulisci e crea struttura
    if os.path.exists(project_dir):
        shutil.rmtree(project_dir)
    
    app_dir = os.path.join(project_dir, 'app')
    package_path = os.path.join(app_dir, 'src', 'main', 'java', *package_name.split('.'))
    assets_path = os.path.join(app_dir, 'src', 'main', 'assets')
    layout_path = os.path.join(app_dir, 'src', 'main', 'res', 'layout')
    res_path = os.path.join(app_dir, 'src', 'main', 'res')
    wrapper_path = os.path.join(project_dir, 'gradle', 'wrapper')
    
    for path in [package_path, assets_path, layout_path, wrapper_path, res_path]:
        os.makedirs(path, exist_ok=True)
    
    # 2. Scrivi file configurazione
    with open(os.path.join(project_dir, 'settings.gradle'), 'w') as f: f.write(get_settings_gradle())
    with open(os.path.join(project_dir, 'build.gradle'), 'w') as f: f.write(get_root_build_gradle())
    with open(os.path.join(app_dir, 'build.gradle'), 'w') as f: f.write(get_app_build_gradle(package_name))
    with open(os.path.join(wrapper_path, 'gradle-wrapper.properties'), 'w') as f: f.write(get_gradle_wrapper_properties())
    with open(os.path.join(project_dir, 'local.properties'), 'w') as f: f.write(get_local_properties(android_sdk_home))

    # 3. MANIFEST & GRAFICA
    manifest_content = ""
    if target_mode == "tv":
        manifest_content = get_android_manifest_tv(package_name, app_name)
        # Passiamo sia l'icona (per il fallback) che il banner esplicito (se esiste)
        generate_tv_banner(icon_path, banner_path, res_path)
    else:
        manifest_content = get_android_manifest(package_name, app_name)

    with open(os.path.join(app_dir, 'src', 'main', 'AndroidManifest.xml'), 'w') as f: f.write(manifest_content)
    with open(os.path.join(package_path, 'MainActivity.java'), 'w') as f: f.write(get_main_activity(package_name))
    with open(os.path.join(layout_path, 'activity_main.xml'), 'w') as f: f.write(get_layout(package_name))

    if icon_path and os.path.exists(icon_path):
        generate_icons(icon_path, res_path)

    print("   - Copia file web...")
    shutil.copytree(web_dir_name, assets_path, dirs_exist_ok=True)

    env_for_gradle = os.environ.copy()
    env_for_gradle["PATH"] = os.path.join(java_home, "bin") + os.pathsep + env_for_gradle["PATH"]

    # 5. Keystore
    print("   - Generazione keystore...")
    keystore_password = "aimods2025"
    keystore_filename = f"{app_name}.keystore"
    key_alias = f"{app_name}_alias"
    
    keytool_command = [
        "keytool", "-genkey", "-v",
        "-keystore", keystore_filename,
        "-alias", key_alias,
        "-keyalg", "RSA", "-keysize", "2048",
        "-validity", "10000",
        "-storepass", keystore_password,
        "-keypass", keystore_password,
        "-dname", f"CN={package_name}, OU=Web2App, O=Web2App, L=Unknown, S=Unknown, C=XX"
    ]
    try:
        subprocess.run(keytool_command, cwd=app_dir, check=True, capture_output=True, text=True, shell=is_windows, env=env_for_gradle)
        props_content = f"storePassword={keystore_password}\nkeyPassword={keystore_password}\nkeyAlias={key_alias}\nstoreFile={keystore_filename}\n"
        with open(os.path.join(app_dir, 'keystore.properties'), 'w') as f: f.write(props_content)
    except Exception as e:
        print(f"❌ Errore keytool: {e}")
        sys.exit(1)

    # Wrapper Setup
    if is_windows:
        gradlew_path = os.path.join(project_dir, 'gradlew.bat')
        with open(gradlew_path, 'w', encoding='utf-8') as f: f.write(get_gradlew_windows_script())
        gradlew_executable = 'gradlew.bat'
    else:
        gradlew_path = os.path.join(project_dir, 'gradlew')
        with open(gradlew_path, 'w', encoding='utf-8') as f: f.write(get_gradlew_unix_script())
        os.chmod(gradlew_path, 0o755)
        gradlew_executable = './gradlew'

    try:
        import urllib.request
        wrapper_jar_url = "https://github.com/gradle/gradle/raw/v8.5.0/gradle/wrapper/gradle-wrapper.jar"
        with urllib.request.urlopen(wrapper_jar_url) as response, open(os.path.join(wrapper_path, 'gradle-wrapper.jar'), 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
    except Exception:
        sys.exit(1)

    print("   - Avvio Build Gradle...")
    try:
        subprocess.run([gradlew_executable, ':app:assembleRelease'], cwd=project_dir, check=True, text=True, shell=is_windows, env=env_for_gradle)
    except subprocess.CalledProcessError as e:
        print(e.stderr)
        sys.exit(1)

    apk_output_dir = "apk_generati"
    os.makedirs(apk_output_dir, exist_ok=True)
    apk_final_name = f"{app_name}{'_TV' if target_mode == 'tv' else ''}.apk"
    apk_final_path = os.path.join(apk_output_dir, apk_final_name)

    candidates = [
        os.path.join(app_dir, 'build', 'outputs', 'apk', 'release', 'app-release.apk'),
        os.path.join(app_dir, 'build', 'outputs', 'apk', 'release', 'app-release-unsigned.apk')
    ]
    found = False
    for p in candidates:
        if os.path.exists(p):
            shutil.move(p, apk_final_path)
            found = True
            break
    
    if found:
        shutil.rmtree(project_dir)
        print(f"\n🎉 FATTO! APK creato in: {os.path.abspath(apk_final_path)}")
    else:
        print("❌ APK non trovato.")

if __name__ == '__main__':
    main()