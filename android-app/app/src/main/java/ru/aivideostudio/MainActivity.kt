package ru.aivideostudio

import android.app.Activity
import android.content.Intent
import android.graphics.Color
import android.net.Uri
import android.os.Bundle
import android.os.Environment
import android.view.Gravity
import android.view.View
import android.widget.*
import androidx.media3.common.MediaItem
import androidx.media3.common.util.UnstableApi
import androidx.media3.transformer.Composition
import androidx.media3.transformer.EditedMediaItem
import androidx.media3.transformer.EditedMediaItemSequence
import androidx.media3.transformer.ExportException
import androidx.media3.transformer.ExportResult
import androidx.media3.transformer.Transformer
import java.io.File

@UnstableApi
class MainActivity : Activity() {
    private val clips = mutableListOf<Uri>()
    private var soundtrack: Uri? = null
    private lateinit var clipInfo: TextView
    private lateinit var soundtrackInfo: TextView
    private lateinit var style: Spinner
    private lateinit var exportButton: Button
    private lateinit var status: TextView
    private var transformer: Transformer? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.statusBarColor = Color.rgb(10, 14, 28)
        window.navigationBarColor = Color.rgb(10, 14, 28)
        buildScreen()
    }

    private fun buildScreen() {
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(20), dp(24), dp(20), dp(20))
            setBackgroundColor(Color.rgb(10, 14, 28))
        }
        val scroll = ScrollView(this)
        val content = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL }
        scroll.addView(content)

        content.addView(label("AI VIDEO STUDIO", 27, Color.WHITE, true))
        content.addView(label("Бесплатный локальный монтаж видео", 16, Color.rgb(170, 184, 211)))
        content.addView(space(20))
        content.addView(label("1. ВИДЕОФРАГМЕНТЫ", 13, Color.rgb(130, 170, 255), true))
        content.addView(button("ДОБАВИТЬ ВИДЕОФАЙЛЫ") { pickVideos() })
        clipInfo = label("Пока не добавлено ни одного видео.", 14, Color.rgb(188, 198, 218))
        content.addView(clipInfo)
        content.addView(button("ОЧИСТИТЬ СПИСОК") {
            clips.clear()
            refreshClipInfo()
        })
        content.addView(space(16))
        content.addView(label("2. ФОНОВАЯ МУЗЫКА (НЕОБЯЗАТЕЛЬНО)", 13, Color.rgb(130, 170, 255), true))
        content.addView(button("ВЫБРАТЬ МУЗЫКУ") { pickAudio() })
        soundtrackInfo = label("Музыка не выбрана.", 14, Color.rgb(188, 198, 218))
        content.addView(soundtrackInfo)
        content.addView(space(16))
        content.addView(label("3. СТИЛЬ ПОРЯДКА КЛИПОВ", 13, Color.rgb(130, 170, 255), true))
        style = Spinner(this).apply {
            adapter = ArrayAdapter(this@MainActivity, android.R.layout.simple_spinner_dropdown_item,
                listOf("Обычный — как добавлены", "Обратный порядок", "Случайный порядок"))
            setPadding(dp(8), dp(4), dp(8), dp(4))
        }
        content.addView(style, matchWrap())
        content.addView(space(20))
        exportButton = button("СОБРАТЬ И СОХРАНИТЬ MP4") { exportVideo() }
        content.addView(exportButton)
        content.addView(space(14))
        status = label("Работает на устройстве. Нет регистрации, API-ключей, подписок и оплаты за экспорт.", 14, Color.rgb(188, 198, 218))
        content.addView(status)
        content.addView(space(18))
        content.addView(label(
            "Текущая версия объединяет выбранные видео в один MP4 и может зациклить отдельную музыкальную дорожку. Длина не задаётся искусственным лимитом: итог ограничен длительностью исходников, свободной памятью и возможностями телефона. Переходы, цветокоррекция, титры, обрезка по таймлайну, AI-сцены и озвучка пока не реализованы.",
            12, Color.rgb(145, 158, 183)
        ))
        root.addView(scroll, LinearLayout.LayoutParams(-1, 0, 1f))
        setContentView(root)
    }

    private fun pickVideos() {
        val intent = Intent(Intent.ACTION_OPEN_DOCUMENT).apply {
            addCategory(Intent.CATEGORY_OPENABLE)
            type = "video/*"
            putExtra(Intent.EXTRA_ALLOW_MULTIPLE, true)
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION)
        }
        startActivityForResult(intent, REQUEST_VIDEOS)
    }

    private fun pickAudio() {
        val intent = Intent(Intent.ACTION_OPEN_DOCUMENT).apply {
            addCategory(Intent.CATEGORY_OPENABLE)
            type = "audio/*"
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION)
        }
        startActivityForResult(intent, REQUEST_AUDIO)
    }

    @Deprecated("Handled for compatibility with the minimum Android version")
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (resultCode != RESULT_OK || data == null) return
        try {
            if (requestCode == REQUEST_VIDEOS) {
                val picked = mutableListOf<Uri>()
                data.clipData?.let { clip ->
                    for (i in 0 until clip.itemCount) picked.add(clip.getItemAt(i).uri)
                } ?: data.data?.let { picked.add(it) }
                picked.forEach { uri ->
                    try { contentResolver.takePersistableUriPermission(uri, Intent.FLAG_GRANT_READ_URI_PERMISSION) } catch (_: Exception) {}
                    if (!clips.contains(uri)) clips.add(uri)
                }
                refreshClipInfo()
            } else if (requestCode == REQUEST_AUDIO) {
                soundtrack = data.data
                soundtrack?.let { uri ->
                    try { contentResolver.takePersistableUriPermission(uri, Intent.FLAG_GRANT_READ_URI_PERMISSION) } catch (_: Exception) {}
                }
                soundtrackInfo.text = if (soundtrack == null) "Музыка не выбрана." else "Фоновая музыка выбрана."
            }
        } catch (e: Exception) {
            status.text = "Не удалось открыть выбранный файл: ${e.message}"
        }
    }

    private fun refreshClipInfo() {
        clipInfo.text = if (clips.isEmpty()) "Пока не добавлено ни одного видео." else "Добавлено видеофайлов: ${clips.size}"
    }

    private fun exportVideo() {
        if (clips.isEmpty()) {
            status.text = "Сначала добавь хотя бы один видеофайл."
            return
        }
        if (transformer != null) {
            status.text = "Экспорт уже выполняется."
            return
        }
        val ordered = when (style.selectedItemPosition) {
            1 -> clips.asReversed()
            2 -> clips.shuffled()
            else -> clips.toList()
        }
        val editedVideos = ordered.map { uri -> EditedMediaItem.Builder(MediaItem.fromUri(uri)).build() }
        val videoSequence = EditedMediaItemSequence.withAudioAndVideoFrom(editedVideos)
        val sequences = mutableListOf(videoSequence)
        soundtrack?.let { audioUri ->
            val audioItem = EditedMediaItem.Builder(MediaItem.fromUri(audioUri)).build()
            val audioSequence = EditedMediaItemSequence.withAudioFrom(listOf(audioItem))
                .buildUpon()
                .setIsLooping(true)
                .build()
            sequences.add(audioSequence)
        }
        val composition = Composition.Builder(sequences).build()
        val moviesDir = getExternalFilesDir(Environment.DIRECTORY_MOVIES) ?: filesDir
        if (!moviesDir.exists()) moviesDir.mkdirs()
        val output = File(moviesDir, "AI_Video_${System.currentTimeMillis()}.mp4")
        exportButton.isEnabled = false
        status.text = "Подготовка экспорта… Не закрывай приложение."
        val listener = object : Transformer.Listener {
            override fun onCompleted(composition: Composition, exportResult: ExportResult) {
                transformer = null
                exportButton.isEnabled = true
                status.text = "Экспорт завершён. Файл: ${output.absolutePath}"
                Toast.makeText(this@MainActivity, "Видео собрано", Toast.LENGTH_LONG).show()
            }

            override fun onError(composition: Composition, exportResult: ExportResult, exportException: ExportException) {
                transformer = null
                exportButton.isEnabled = true
                status.text = "Ошибка экспорта: ${exportException.message ?: "неизвестная ошибка"}"
            }
        }
        try {
            transformer = Transformer.Builder(this).addListener(listener).build()
            transformer!!.start(composition, output.absolutePath)
            status.text = "Идёт локальный экспорт MP4…"
        } catch (e: Exception) {
            transformer = null
            exportButton.isEnabled = true
            status.text = "Не удалось начать экспорт: ${e.message}"
        }
    }

    private fun button(text: String, action: () -> Unit) = Button(this).apply {
        this.text = text
        isAllCaps = false
        setTextColor(Color.WHITE)
        setBackgroundTintList(android.content.res.ColorStateList.valueOf(Color.rgb(48, 76, 150)))
        setOnClickListener { action() }
    }

    private fun label(text: String, size: Int, color: Int, bold: Boolean = false) =
        TextView(this).apply {
            this.text = text
            textSize = size.toFloat()
            setTextColor(color)
            if (bold) setTypeface(null, android.graphics.Typeface.BOLD)
            setPadding(0, dp(6), 0, dp(6))
        }

    private fun space(height: Int) = View(this).apply { layoutParams = LinearLayout.LayoutParams(1, dp(height)) }
    private fun matchWrap() = LinearLayout.LayoutParams(-1, -2).apply { bottomMargin = dp(4) }
    private fun dp(value: Int) = (value * resources.displayMetrics.density).toInt()

    companion object {
        private const val REQUEST_VIDEOS = 101
        private const val REQUEST_AUDIO = 102
    }
}
