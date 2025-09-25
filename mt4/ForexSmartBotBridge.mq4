//+------------------------------------------------------------------+
//|                                                ForexSmartBotBridge|
//|                                     ZeroMQ bridge for MT4 <-> Py  |
//+------------------------------------------------------------------+
#property strict

#include <WinSock2.mqh>
#import "shell32.dll"
   int ShellExecuteA(int hwnd,string lpOperation,string lpFile,string lpParameters,string lpDirectory,int nShowCmd);
#import

extern string ServerHost = "127.0.0.1";
extern int    ServerPort = 5555;

// NOTE: This is a *minimal* illustrative EA to show a JSON/ZeroMQ pattern.
// In production, prefer a robust 3rd-party MT4<->Python ZeroMQ bridge template.
// Due to MQL4 limitations, a full robust ZMQ client is not provided here.
// Replace this stub with your preferred bridge EA.

int OnInit(){ Print("ForexSmartBotBridge loaded. Configure a proper ZMQ EA."); return(INIT_SUCCEEDED); }
void OnDeinit(const int reason){}
void OnTick(){ /* no-op */ }
