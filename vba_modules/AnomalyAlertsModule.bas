Attribute VB_Name = "AnomalyAlertsModule"
Option Explicit

' ==============================================================================
' Financial Trade Monitoring System - Excel VBA Automation Module
' Purpose: Trader Sign-Off, Alert Filtering, and Operations Audit Trail Logging
' ==============================================================================

Public Sub FilterCriticalAlerts()
    Dim ws As Worksheet
    Set ws = ThisWorkbook.Sheets("Critical & High Alerts")
    
    ws.Activate
    If ws.AutoFilterMode Then ws.AutoFilterMode = False
    
    ' Apply Autofilter on Range starting at row 7
    ' Column 11 is RiskTier
    ws.Range("A7:W" & ws.Cells(ws.Rows.Count, "A").End(xlUp).Row).AutoFilter Field:=11, Criteria1:="CRITICAL", Operator:=xlOr, Criteria2:="HIGH"
    
    MsgBox "Filtered to display CRITICAL and HIGH risk alerts.", vbInformation, "Trade Alerts Filter"
End Sub

Public Sub ShowAllAlerts()
    Dim ws As Worksheet
    Set ws = ThisWorkbook.Sheets("Critical & High Alerts")
    
    ws.Activate
    If ws.FilterMode Then
        ws.ShowAllData
    End If
    MsgBox "All alerts displayed.", vbInformation, "Trade Alerts Filter"
End Sub

Public Sub AcknowledgeTrade()
    Dim ws As Worksheet
    Dim selectedRow As Long
    Dim tradeID As String
    Dim traderName As String
    
    Set ws = ThisWorkbook.Sheets("Critical & High Alerts")
    selectedRow = Selection.Row
    
    ' Validate selection is within data range (starts at row 8)
    If selectedRow < 8 Or ws.Cells(selectedRow, 1).Value = "" Then
        MsgBox "Please select a valid trade row in the alerts table.", vbExclamation, "Invalid Selection"
        Exit Sub
    End If
    
    tradeID = ws.Cells(selectedRow, 1).Value
    traderName = InputBox("Enter Trader / Analyst Name for Sign-Off on Trade [" & tradeID & "]:", "Trader Sign-Off", Environ("USERNAME"))
    
    If Trim(traderName) = "" Then
        MsgBox "Sign-off cancelled. Trader name is required.", vbWarning, "Cancelled"
        Exit Sub
    End If
    
    ' Update Status and Timestamp columns (Columns V & W)
    ' Assuming Column V is 'SignOffStatus' and Column W is 'SignOffTimestamp'
    ws.Cells(selectedRow, 22).Value = "ACKNOWLEDGED - " & UCase(traderName)
    ws.Cells(selectedRow, 22).Interior.Color = RGB(198, 239, 206) ' Soft Light Green
    ws.Cells(selectedRow, 22).Font.Color = RGB(0, 97, 0)
    
    ws.Cells(selectedRow, 23).Value = Format(Now, "yyyy-mm-dd hh:mm:ss")
    
    MsgBox "Trade " & tradeID & " successfully acknowledged by " & traderName & ".", vbInformation, "Sign-Off Recorded"
End Sub

Public Sub ExportAuditLog()
    Dim ws As Worksheet
    Dim fso As Object, stream As Object
    Dim csvPath As String
    Dim lastRow As Long, i As Long
    Dim tradeID As String, status As String, signTime As String
    
    Set ws = ThisWorkbook.Sheets("Critical & High Alerts")
    lastRow = ws.Cells(ws.Rows.Count, 1).End(xlUp).Row
    
    csvPath = ThisWorkbook.Path & "\trader_audit_signoff_log.csv"
    
    Set fso = CreateObject("Scripting.FileSystemObject")
    Set stream = fso.CreateTextFile(csvPath, True)
    
    ' Header
    stream.WriteLine "TradeID,ExecutionTime,Instrument,Quantity,Price,Counterparty,RiskTier,PrimaryAnomalyReason,SignOffStatus,SignOffTimestamp"
    
    Dim ackCount As Long
    ackCount = 0
    
    For i = 8 To lastRow
        status = CStr(ws.Cells(i, 22).Value)
        If InStr(1, status, "ACKNOWLEDGED", vbTextCompare) > 0 Then
            stream.WriteLine ws.Cells(i, 1).Value & "," & _
                             ws.Cells(i, 2).Value & "," & _
                             ws.Cells(i, 6).Value & "," & _
                             ws.Cells(i, 3).Value & "," & _
                             ws.Cells(i, 4).Value & "," & _
                             ws.Cells(i, 5).Value & "," & _
                             ws.Cells(i, 11).Value & "," & _
                             """" & ws.Cells(i, 12).Value & """" & "," & _
                             """" & status & """" & "," & _
                             ws.Cells(i, 23).Value
            ackCount = ackCount + 1
        End If
    Next i
    
    stream.Close
    
    MsgBox "Successfully exported " & ackCount & " acknowledged trades to:" & vbCrLf & csvPath, vbInformation, "Audit Log Export Complete"
End Sub
