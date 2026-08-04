#include <WiFi.h>
#include <WiFiManager.h>
#include <WebServer.h>
#include <Arduino.h>
#include <IRremoteESP8266.h>
#include <IRsend.h>
#include <vector>



// ========== 文件开头，自定义路径名，修改这里即可 ==========
const String controllerPath = "/local_mcp/controller__air_conditioner__bedroom";
const String apName = "local_mcp.controller__air_conditioner__bedroom";
// ========================================================


// ======================== 【1. 基础单条红外指令】 ========================
struct RawCommand {const char* cmdName; std::vector<uint16_t> rawData;};
const std::vector<RawCommand> rawCmdList = {
{"开启",{9040,  4498,  614,  1654,  618,  1656,  620,  542,  600,  542,  600,  526,  618,  526,  620,  1652,  652,  1630,  622,  1692,  582,  1654,  618,  1654,  620,  542,  626,  1632,  616,  1656,  624,  1654,  624,  524,  618,  524,  614,  528,  614,  528,  616,  526,  618,  526,  616,  1658,  620,  1658,  620,  1658,  620,  526,  610,  530,  588,  554,  612,  530,  616,  526,  616,  530,  616,  528,  618,  528,  618,  528,  610,  530,  612,  530,  614,  528,  614,  528,  616,  1658,  620,  1658,  620,  528,  614,  528,  610,  530,  612,  528,  614,  528,  616,  528,  616,  528,  618,  528,  618,  528,  614,  528,  610,  530,  612,  530,  614,  528,  614,  530,  614,  1660,  618,  530,  618,  528,  614,  530,  610,  530,  612,  530,  614,  528,  614,  530,  614,  528,  618,  530,  616,  528,  614,  530,  610,  530,  614,  528,  614,  528,  614,  528,  616,  528,  618,  530,  620,  528,  614,  528,  612,  528,  614,  528,  614,  528,  614,  528,  614,  1660,  620,  528,  618,  530,  614,  530,  612,  532,  610,  532,  610,  532,  612,  532,  612,  532,  614,  532,  616,  532,  612,  1662,  610,  532,  608,  1664,  610,  534,  608,  534,  610,  536,  610,  536,  610,  538,  606,  1668,  604,  1702,  570,  1684,  590,  1684,  590,  1684,  592,  1686,  592,  554,  592,  1706,  568}},
{"关闭",{8996,  4500,  598,  1640,  602,  1640,  600,  522,  598,  520,  596,  522,  598,  524,  598,  1644,  598,  1640,  598,  1642,  598,  1642,  598,  1642,  598,  522,  598,  1644,  598,  522,  598,  522,  598,  1642,  598,  522,  598,  522,  598,  524,  596,  522,  598,  522,  598,  1644,  598,  1642,  598,  1642,  598,  522,  598,  522,  598,  522,  598,  524,  598,  522,  598,  522,  598,  522,  598,  522,  598,  522,  598,  522,  598,  522,  598,  522,  596,  524,  598,  1644,  596,  524,  596,  1644,  596,  524,  598,  522,  598,  522,  598,  524,  598,  522,  598,  522,  598,  522,  598,  522,  596,  524,  596,  524,  596,  524,  596,  524,  596,  524,  596,  1644,  594,  526,  594,  526,  596,  524,  596,  526,  594,  526,  594,  526,  594,  526,  594,  526,  594,  526,  594,  528,  592,  526,  594,  528,  592,  530,  592,  548,  572,  548,  572,  548,  572,  548,  572,  548,  572,  548,  572,  548,  572,  550,  570,  550,  572,  550,  570,  550,  570,  550,  570,  550,  570,  550,  568,  552,  568,  552,  568,  554,  566,  554,  566,  554,  564,  556,  564,  556,  562,  1680,  560,  582,  538,  1702,  536,  584,  536,  584,  538,  582,  536,  584,  536,  584,  536,  1704,  536,  1704,  536,  1704,  536,  1704,  538,  1704,  536,  1706,  534,  1704,  536,  1704,  536}},
{"标准模式",{9040,  4498,  614,  1654,  618,  1656,  620,  542,  600,  542,  600,  526,  618,  526,  620,  1652,  652,  1630,  622,  1692,  582,  1654,  618,  1654,  620,  542,  626,  1632,  616,  1656,  624,  1654,  624,  524,  618,  524,  614,  528,  614,  528,  616,  526,  618,  526,  616,  1658,  620,  1658,  620,  1658,  620,  526,  610,  530,  588,  554,  612,  530,  616,  526,  616,  530,  616,  528,  618,  528,  618,  528,  610,  530,  612,  530,  614,  528,  614,  528,  616,  1658,  620,  1658,  620,  528,  614,  528,  610,  530,  612,  528,  614,  528,  616,  528,  616,  528,  618,  528,  618,  528,  614,  528,  610,  530,  612,  530,  614,  528,  614,  530,  614,  1660,  618,  530,  618,  528,  614,  530,  610,  530,  612,  530,  614,  528,  614,  530,  614,  528,  618,  530,  616,  528,  614,  530,  610,  530,  614,  528,  614,  528,  614,  528,  616,  528,  618,  530,  620,  528,  614,  528,  612,  528,  614,  528,  614,  528,  614,  528,  614,  1660,  620,  528,  618,  530,  614,  530,  612,  532,  610,  532,  610,  532,  612,  532,  612,  532,  614,  532,  616,  532,  612,  1662,  610,  532,  608,  1664,  610,  534,  608,  534,  610,  536,  610,  536,  610,  538,  606,  1668,  604,  1702,  570,  1684,  590,  1684,  590,  1684,  592,  1686,  592,  554,  592,  1706,  568}},
{"睡眠模式",{9008,  4528,  602,  1668,  582,  1690,  582,  560,  604,  536,  586,  560,  584,  558,  612,  1686,  568,  1688,  588,  1692,  580,  1690,  584,  1690,  584,  560,  606,  538,  606,  1666,  586,  582,  566,  1690,  584,  562,  580,  562,  578,  562,  580,  562,  608,  576,  542,  1692,  586,  1690,  588,  1694,  608,  538,  606,  572,  542,  564,  580,  562,  582,  560,  582,  562,  586,  562,  584,  564,  606,  540,  576,  624,  518,  562,  580,  564,  580,  564,  582,  1712,  590,  1668,  584,  564,  580,  600,  544,  600,  540,  600,  566,  540,  606,  578,  564,  560,  562,  584,  564,  1714,  582,  584,  536,  600,  570,  538,  604,  576,  540,  628,  540,  1668,  586,  584,  562,  628,  540,  598,  544,  598,  520,  624,  514,  606,  538,  628,  516,  606,  566,  560,  562,  606,  538,  624,  514,  628,  516,  628,  516,  628,  516,  606,  536,  610,  538,  608,  538,  630,  538,  600,  516,  626,  516,  628,  540,  604,  514,  630,  514,  1716,  562,  608,  538,  608,  536,  628,  538,  600,  514,  630,  514,  630,  512,  630,  538,  586,  536,  610,  538,  630,  514,  626,  540,  602,  514,  630,  512,  630,  514,  630,  512,  632,  514,  610,  536,  630,  512,  630,  536,  1738,  512,  630,  512,  1764,  514,  632,  536,  1718,  560,  1716,  560,  606,  512}}
};




// ======================== 【2. 组合/定时指令定义】 ========================
#define SECONDS(s) ((uint32_t)(s) * 1000UL)
#define MINUTES(m) ((uint32_t)(m) * 60 * 1000UL)
#define HOURS(h) ((uint32_t)(h) * 60 * 60 * 1000UL)
struct SeqStep {const char* cmdName; uint32_t delayAfter;};
struct SequenceCommand {const char* seqName; std::vector<SeqStep> steps;};
const std::vector<SequenceCommand> seqCmdList = {
{"午睡模式",{            {"标准模式", 600000UL},
            {"睡眠模式", 1800000UL},
            {"关闭", 0UL}}},
{"快速测试",{            {"开启", 5000UL},
            {"睡眠模式", 5000UL},
            {"关闭", 0UL}}}
};
// ==============================================================================





const uint8_t kIrLed = 4;
const uint16_t IR_CARRIER_FREQ = 36800;
IRsend irsend(kIrLed);
WebServer server(8051);



// ========== LED状态指示 ESP32‑C3 GPIO8低电平点亮 ==========
#define LED_BUILTIN 8
#define LED_ON_LEVEL LOW
#define LED_OFF_LEVEL HIGH
// #define LED_BUILTIN LED_BUILTIN
// #define LED_ON_LEVEL HIGH
// #define LED_OFF_LEVEL LOW



// ======================== wifi相关 ========================
const unsigned long connectTimeout = 20;
const unsigned long configPortalTimeout = 60;
const unsigned long reconnectDelay = 5000;
unsigned long lastReconnectAttempt = 0;

void wifiSetup()
{
  Serial.println("Connecting WiFi...");
  WiFiManager wm;
  wm.setConnectTimeout(connectTimeout);
  wm.setConfigPortalTimeout(configPortalTimeout);
  wm.setBreakAfterConfig(true);
  wm.setCleanConnect(true);

  bool res = wm.autoConnect(apName.c_str(), "12345678");
  if (!res)
  {
    Serial.println("初始连接失败，正在重启...");
    ESP.restart();
  }
  else
  {
    Serial.println("已成功连接 WiFi!");
    digitalWrite(LED_BUILTIN, LED_OFF_LEVEL); //wifi连上熄灭LED
  }
}

void wifiLoop()
{
  if (WiFi.status() != WL_CONNECTED)
  {
    digitalWrite(LED_BUILTIN, LED_ON_LEVEL); //WiFi断开，点亮LED
    unsigned long currentMillis = millis();
    if (currentMillis - lastReconnectAttempt >= reconnectDelay)
    {
      lastReconnectAttempt = currentMillis;
      Serial.println("WiFi 断开，正在尝试重连...");
      WiFi.disconnect(true);
      WiFiManager wm;
      bool res = wm.autoConnect(apName.c_str(), "12345678");
      if (!res)
      {
        Serial.println("重连失败，将重启设备...");
        delay(1000);
        ESP.restart();
      }
      else
      {
        Serial.println("重连成功 :)");
      }
    }
  }
}
// ======================================================




// ======================== 【3. 非阻塞异步任务引擎】 ========================
bool isTaskRunning = false;
std::vector<SeqStep> activeTaskSteps;
size_t currentStepIdx = 0;
unsigned long lastStepTime = 0;
uint32_t currentWaitDelay = 0;

// 根据名称找红外数据并发射
bool sendRawByName(const char* name) {
    for (const auto& rawCmd : rawCmdList) {
        if (String(name) == String(rawCmd.cmdName)) {
            Serial.print("【发射红外】 -> ");
            Serial.println(rawCmd.cmdName);
            irsend.sendRaw(rawCmd.rawData.data(), rawCmd.rawData.size(), IR_CARRIER_FREQ);
            return true;
        }
    }
    Serial.print("【错误】未找到名字为 '");
    Serial.print(name);
    Serial.println("' 的红外波形数据！");
    return false;
}

// 接收 HTTP 指令处理函数
void handleACIR()
{
    String cmd = server.arg("cmd");
    bool matchFound = false;
    std::vector<SeqStep> newSteps;

    // 1. 先去组合指令列表寻找
    for (const auto& seq : seqCmdList) {
        if (cmd == String(seq.seqName)) {
            newSteps = seq.steps;
            matchFound = true;
            break;
        }
    }

    // 2. 如果组合指令没找到，再去单条指令列表寻找
    if (!matchFound) {
        for (const auto& raw : rawCmdList) {
            if (cmd == String(raw.cmdName)) {
                // 如果是单条指令，直接当作只包含 1 个步骤且延迟为 0 的任务
                newSteps.push_back({raw.cmdName, 0});
                matchFound = true;
                break;
            }
        }
    }

    if (matchFound) {
        // 装载新任务（会自动覆盖/打断当前正在执行的旧任务）
        activeTaskSteps = newSteps;
        currentStepIdx = 0;
        lastStepTime = millis();
        currentWaitDelay = 888; // 收到 HTTP 请求后延迟 888ms 再发第一条，确保 HTTP 响应先顺利发回
        isTaskRunning = true;

        String okJson = R"({"success":true,"cmd":")" + cmd + R"(","msg":"指令/组合已启动"})";
        server.send(200, "application/json", okJson);
    } else {
        String errJson = R"({"success":false,"msg":" 未知 cmd 指令 "})";
        server.send(400, "application/json", errJson);
    }
}

void setup()
{
    Serial.begin(115200);
    delay(200);

    pinMode(LED_BUILTIN, OUTPUT);
    digitalWrite(LED_BUILTIN, LED_ON_LEVEL); //通电直接亮灯

    wifiSetup();
    delay(200);
    irsend.begin();
    delay(200);

    server.on(controllerPath.c_str(), handleACIR);
    server.begin();
    Serial.println("HTTP 服务器已启动，端口: 8051");
}

void loop()
{
    wifiLoop();
    server.handleClient();

    // 异步任务调度核心：完全不打断 loop，不阻塞 WiFi
    if (isTaskRunning) {
        if (millis() - lastStepTime >= currentWaitDelay) {
            if (currentStepIdx < activeTaskSteps.size()) {
                // 1. 取出当前步骤
                SeqStep step = activeTaskSteps[currentStepIdx];

                // 2. 发射红外
                sendRawByName(step.cmdName);
                delay(66);
                sendRawByName(step.cmdName);
                delay(66);
                sendRawByName(step.cmdName);

                // 3. 记录时间，准备进入下一个等待期
                lastStepTime = millis();
                currentWaitDelay = step.delayAfter;
                currentStepIdx++;

                if (currentWaitDelay > 0) {
                    Serial.print("【定时任务】等待中... 预计 ");
                    Serial.print(currentWaitDelay / 1000);
                    Serial.println(" 秒后执行下一个动作");
                }
            } else {
                // 所有步骤执行完毕
                isTaskRunning = false;
                Serial.println("【定时任务】当前序列全部执行完毕！");
            }
        }
    }
}




