/*
Copyright (c) 2010  Sybase, Inc.

Module Name:
	odbcloblocator.cpp

Abstract:
 	Sample ODBC console application.
 	Demonstrates the use of the ODBC LOB locator feature.

	To run this sample, update dsn, username, and password below.
*/

#if defined (WIN32) || defined(_WIN32)
#include <windows.h>
#else
#include <stdlib.h>
#include <stddef.h>
#endif
#include <string.h>
#include <stdio.h>
#include <sql.h>
#include <sqlext.h>
#include "sybasesqltypes.h"
#include <iostream>
#ifdef	LINUX
#ifndef SQLLEN
#define SQLLEN SQLINTEGER
#endif
#ifndef SQLULEN
#define SQLULEN SQLUINTEGER
#endif
#endif
#ifndef _ODBCSTRTYPE
#if defined(UNICODE) || defined(_UNICODE)
#define _ODBCSTRTYPE(str)		(SQLWCHAR *)L##str
#else
#define _ODBCSTRTYPE(str)		(SQLCHAR *)str
#endif
#endif
#ifndef TCOUT
#if defined(UNICODE) || defined(_UNICODE)
#define TCOUT		wcout
#else
#define TCOUT		cout
#endif
#endif
#ifndef TCIN
#if defined(UNICODE) || defined(_UNICODE)
#define TCIN(str,len)		wcin.getline((wchar_t*)str, len)
#else
#define TCIN(str,len)		cin.getline((char*)str, len)
#endif
#endif

using namespace std;

#define ERR_MSG_LEN	255

SQLTCHAR* createTableStmt = _ODBCSTRTYPE("create table odbcloblocator (c1 int, c2 text null, c3 unitext null, c4 image null)");
SQLTCHAR* dropTableStmt = _ODBCSTRTYPE("drop table odbcloblocator");
SQLTCHAR* insertStmt = _ODBCSTRTYPE("insert into odbcloblocator values (?, ?, ?, ?)");
SQLTCHAR* selectStmt = _ODBCSTRTYPE("select c1, return_lob(text, create_locator(text_locator, c2)), return_lob(unitext, create_locator(unitext_locator, c3)), return_lob(image, create_locator(image_locator, c4)) from odbcloblocator");
SQLTCHAR* createTEXT_LOC_SQL = _ODBCSTRTYPE("{CALL sp_drv_create_text_locator(?)}");
SQLTCHAR* createUNITEXT_LOC_SQL = _ODBCSTRTYPE("{CALL sp_drv_create_unitext_locator(?)}");
SQLTCHAR* createIMAGE_LOC_SQL = _ODBCSTRTYPE("{CALL sp_drv_create_image_locator(?)}");
SQLTCHAR* selectCOL_SQL = _ODBCSTRTYPE("SELECT c2, c3, c4 FROM odbcloblocator WHERE c1 = ?");
SQLTCHAR* substringTEXT_SQL = _ODBCSTRTYPE("{CALL sp_drv_text_substring(?, ?, ?)}");
SQLTCHAR* substringUNITEXT_SQL = _ODBCSTRTYPE("{CALL sp_drv_unitext_substring(?, ?, ?)}");
SQLTCHAR* substringIMAGE_SQL = _ODBCSTRTYPE("{CALL sp_drv_image_substring(?, ?, ?)}");
SQLTCHAR* setdataTEXT_SQL = _ODBCSTRTYPE("{CALL sp_drv_text_setdata(?, ?, ?, ?)}");
SQLTCHAR* setdataUNITEXT_SQL = _ODBCSTRTYPE("{CALL sp_drv_unitext_setdata(?, ?, ?, ?)}");
SQLTCHAR* setdataIMAGE_SQL = _ODBCSTRTYPE("{CALL sp_drv_image_setdata(?, ?, ?, ?)}");
SQLTCHAR* setdataTEXT_LOC_SQL = _ODBCSTRTYPE("{CALL sp_drv_text_locator_setdata(?, ?, ?, ?)}");
SQLTCHAR* setdataIMAGE_LOC_SQL = _ODBCSTRTYPE("{CALL sp_drv_image_locator_setdata(?, ?, ?, ?)}");
SQLTCHAR* setdataUNITEXT_LOC_SQL = _ODBCSTRTYPE("{CALL sp_drv_unitext_locator_setdata(?, ?, ?, ?)}");
SQLTCHAR* truncateLOB_SQL = _ODBCSTRTYPE("TRUNCATE LOB ? (?)");
SQLTCHAR* TLTTSQL = _ODBCSTRTYPE("{CALL sp_drv_locator_to_text(?)}");
SQLTCHAR* UTLTUTSQL = _ODBCSTRTYPE("{CALL sp_drv_locator_to_unitext(?)}");
SQLTCHAR* ILTISQL = _ODBCSTRTYPE("{CALL sp_drv_locator_to_image(?)}");
SQLTCHAR* deallocateLOC_SQL = _ODBCSTRTYPE("DEALLOCATE LOCATOR ?");
SQLTCHAR* charLEN_TEXT_SQL = _ODBCSTRTYPE("{CALL sp_drv_text_locator_charlength(?, ?)}");
SQLTCHAR* charLEN_UNITEXT_SQL = _ODBCSTRTYPE("{CALL sp_drv_unitext_locator_charlength(?, ?)}");
SQLTCHAR* byteLEN_TEXT_SQL = _ODBCSTRTYPE("{CALL sp_drv_text_locator_bytelength(?, ?)}");
SQLTCHAR* byteLEN_UNITEXT_SQL = _ODBCSTRTYPE("{CALL sp_drv_unitext_locator_bytelength(?, ?)}");
SQLTCHAR* byteLEN_IMAGE_SQL = _ODBCSTRTYPE("{CALL sp_drv_image_locator_bytelength(?, ?)}");
SQLTCHAR* charINDEX_TEXT_SQL = _ODBCSTRTYPE("{CALL sp_drv_text_locator_charindex(?, ?, ?, ?)}");
SQLTCHAR* charINDEX_UNITEXT_SQL = _ODBCSTRTYPE("{CALL sp_drv_image_locator_charindex(?, ?, ?, ?)}");
SQLTCHAR* varcharINDEX_SQL = _ODBCSTRTYPE("{CALL sp_drv_varchar_charindex(?, ?, ?, ?)}");
SQLTCHAR* varbinINDEX_SQL = _ODBCSTRTYPE("{CALL sp_drv_varbinary_charindex(?, ?, ?, ?)}");
SQLTCHAR* patINDEX_SQL = _ODBCSTRTYPE("{CALL sp_drv_text_locator_patindex(?, ?, ?)}");
SQLTCHAR* validTEXT_LOC_SQL = _ODBCSTRTYPE("{CALL sp_drv_text_locator_valid(?, ?)}");
SQLTCHAR* validUNITEXT_LOC_SQL = _ODBCSTRTYPE("{CALL sp_drv_unitext_locator_valid(?, ?)}");
SQLTCHAR* validIMAGE_LOC_SQL = _ODBCSTRTYPE("{CALL sp_drv_image_locator_valid(?, ?)}");

#if defined(WIN32) && defined(UNICODE)
void connect(SQLHENV* env, SQLHDBC* dbc, SQLHSTMT* stmt, int argc, wchar_t* argv[]);
#else
void connect(SQLHENV* env, SQLHDBC* dbc, SQLHSTMT* stmt, int argc, char* argv[]);
#endif
void finish(SQLHENV env, SQLHDBC dbc, SQLHSTMT stmt, bool doExit);
void createTable(SQLHSTMT stmt);
void dropTable(SQLHSTMT stmt);
void CreateLocatorFromClient(SQLHDBC dbc, SQLHSTMT stmt);
void Substring(SQLHDBC dbc, SQLHSTMT stmt);
void Setdata(SQLHDBC dbc, SQLHSTMT stmt);
void Setdata_append(SQLHDBC dbc, SQLHSTMT stmt);
void Truncate(SQLHDBC dbc, SQLHSTMT stmt);
void ReturnLOB(SQLHDBC dbc, SQLHSTMT stmt);
void CharLength(SQLHDBC dbc, SQLHSTMT stmt);
void ByteLength(SQLHDBC dbc, SQLHSTMT stmt);
void IndexofLocator(SQLHDBC dbc, SQLHSTMT stmt);
void Indexof(SQLHDBC dbc, SQLHSTMT stmt);
void PatternIndexof(SQLHDBC dbc, SQLHSTMT stmt);
void LocatorValid(SQLHDBC dbc, SQLHSTMT stmt);
void Deallocate(SQLHDBC dbc, SQLHSTMT stmt);
void printTable(SQLHSTMT stmt);
void printBinary(unsigned char* data, int length);
void printError(SQLRETURN retcode, SQLSMALLINT handleType, SQLHANDLE handle);
void sqlok(SQLHSTMT stmt, SQLRETURN retcode, char* message);

#if defined(WIN32) && defined(UNICODE)
int wmain(int argc, wchar_t* argv[])
#else
int main(int argc, char* argv[])
#endif
{
	SQLHENV env = SQL_NULL_HANDLE;
	SQLHDBC dbc = SQL_NULL_HANDLE;
	SQLHSTMT stmt = SQL_NULL_HANDLE;
	connect(&env, &dbc, &stmt, argc, argv);
	createTable(stmt);
	CreateLocatorFromClient(dbc, stmt);
	Substring(dbc, stmt);
	Setdata(dbc, stmt);
	Setdata_append(dbc, stmt);
	Truncate(dbc, stmt);
	ReturnLOB(dbc, stmt);
	CharLength(dbc, stmt);
	ByteLength(dbc, stmt);
	IndexofLocator(dbc, stmt);
	Indexof(dbc, stmt);
	PatternIndexof(dbc, stmt);
	LocatorValid(dbc, stmt);
	Deallocate(dbc, stmt);
	printTable(stmt);
	finish(env, dbc, stmt, false);
	return 0;
}
void printBinary(unsigned char* data, int length)
{
	unsigned char chars[16] = {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F'};

	for (int i = 0; i < length; i++)
	{
		cout << chars[data[i] / 16];
		cout << chars[data[i] & 0x0f];
	}

	cout << endl;
}
void CreateLocatorFromClient(SQLHDBC dbc, SQLHSTMT stmt)
{
	SQLRETURN sr;
	sr = SQLSetConnectAttr(dbc, SQL_ATTR_AUTOCOMMIT, (SQLPOINTER)SQL_AUTOCOMMIT_OFF, 0);
	printError(sr, SQL_HANDLE_STMT, stmt);
	int c1 = 0;
	SQLLEN l1 = sizeof(int);
	SQLCHAR c2LOB[2401] = "A common mistake is to consider \"iterative\" and \"incremental\" as synonyms, \
which they are not. In software/systems development, however, they typically go \
hand in hand. The basic idea is to develop a system through repeated cycles (ite\
rative) and in smaller portions at a time (incremental), allowing the developer \
to take advantage of what was learned during the development of earlier portions\
or versions of the system. Learning comes from both the development and use of t\
he system, where possible key steps in the process start with a simple implement\
ation of a subset of the software requirements and iteratively enhance the evolv\
ing versions until the full system is implemented. At each iteration, design mod\
ifications are made and new functional capabilities are added. The procedure its\
elf consists of the initialization step, the iteration step, and the Project Con\
trol List. The initialization step creates a base version of the system. The goa\
l for this initial implementation is to create a product to which the user can r\
eact. It should offer a sampling of the key aspects of the problem and provide a\
solution that is simple enough to understand and implement easily. To guide the \
iteration process, a project control list is created that contains a record of a\
ll tasks that need to be performed. It includes such items as new features to be\
implemented and areas of redesign of the existing solution. The control list is \
constantly being revised as a result of the analysis phase. The iteration involv\
es the redesign and implementation of a task from the project control list, and \
the analysis of the current version of the system. The goal for the design and i\
mplementation of any iteration is to be simple, straightforward, and modular, su\
pporting redesign at that stage or as a task added to the project control list. \
The level of design detail is not dictated by the interactive approach. In a lig\
ht-weight iterative project the code may represent the major source of documenta\
tion of the system; however, in a mission-critical iterative project a formal So\
ftware Design Document may be used. The analysis of an iteration is based upon u\
ser feedback, and the program analysis facilities available. It involves analysi\
s of the structure, modularity, usability, reliability, efficiency, & achievemen\
t of goals. The project control list is modified in light of the analysis results.";
	SQLLEN l2LOB = sizeof(c2LOB);
	unsigned char c2LOC[SQL_LOCATOR_SIZE];
	SQLLEN l2LOC = sizeof(c2LOC);
	SQLWCHAR c3LOB[2401];
	memcpy(c3LOB, L"A common mistake is to consider \"iterative\" and \"incremental\" as synonyms, \
which they are not. In software/systems development, however, they typically go \
hand in hand. The basic idea is to develop a system through repeated cycles (ite\
rative) and in smaller portions at a time (incremental), allowing the developer \
to take advantage of what was learned during the development of earlier portions\
or versions of the system. Learning comes from both the development and use of t\
he system, where possible key steps in the process start with a simple implement\
ation of a subset of the software requirements and iteratively enhance the evolv\
ing versions until the full system is implemented. At each iteration, design mod\
ifications are made and new functional capabilities are added. The procedure its\
elf consists of the initialization step, the iteration step, and the Project Con\
trol List. The initialization step creates a base version of the system. The goa\
l for this initial implementation is to create a product to which the user can r\
eact. It should offer a sampling of the key aspects of the problem and provide a\
solution that is simple enough to understand and implement easily. To guide the \
iteration process, a project control list is created that contains a record of a\
ll tasks that need to be performed. It includes such items as new features to be\
implemented and areas of redesign of the existing solution. The control list is \
constantly being revised as a result of the analysis phase. The iteration involv\
es the redesign and implementation of a task from the project control list, and \
the analysis of the current version of the system. The goal for the design and i\
mplementation of any iteration is to be simple, straightforward, and modular, su\
pporting redesign at that stage or as a task added to the project control list. \
The level of design detail is not dictated by the interactive approach. In a lig\
ht-weight iterative project the code may represent the major source of documenta\
tion of the system; however, in a mission-critical iterative project a formal So\
ftware Design Document may be used. The analysis of an iteration is based upon u\
ser feedback, and the program analysis facilities available. It involves analysi\
s of the structure, modularity, usability, reliability, efficiency, & achievemen\
t of goals. The project control list is modified in light of the analysis results.", 2401 * sizeof(SQLWCHAR));
	SQLLEN l3LOB = sizeof(c3LOB);
	unsigned char c3LOC[SQL_LOCATOR_SIZE];
	SQLLEN l3LOC = sizeof(c3LOC);
	unsigned char c4LOB[2401];

	for (int i = 0; i < 2401; i++)
	{
		c4LOB[i] = (char)i;
	}

	SQLLEN l4LOB = sizeof(c4LOB);
	unsigned char c4LOC[SQL_LOCATOR_SIZE];
	SQLLEN l4LOC = sizeof(c4LOC);
	//First we will move the data from the client to the server so we can reference it by locators
	//TEXT locator
	sr = SQLBindParameter(stmt, 1, SQL_PARAM_INPUT, SQL_C_CHAR, SQL_CHAR, l2LOB, 0, c2LOB, l2LOB, &l2LOB);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLExecDirect(stmt, createTEXT_LOC_SQL, SQL_NTS);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLBindCol(stmt, 1, SQL_C_TEXT_LOCATOR, c2LOC, l2LOC, &l2LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLFetch(stmt);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLFreeStmt(stmt, SQL_UNBIND);
	sr = SQLFreeStmt(stmt, SQL_RESET_PARAMS);
	sr = SQLFreeStmt(stmt, SQL_CLOSE);
	//UNITEXT locator
	sr = SQLBindParameter(stmt, 1, SQL_PARAM_INPUT, SQL_C_WCHAR, SQL_WCHAR, l3LOB, 0, c3LOB, l3LOB, &l3LOB);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLExecDirect(stmt, createUNITEXT_LOC_SQL, SQL_NTS);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLBindCol(stmt, 1, SQL_C_UNITEXT_LOCATOR, c3LOC, l3LOC, &l3LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLFetch(stmt);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLFreeStmt(stmt, SQL_UNBIND);
	sr = SQLFreeStmt(stmt, SQL_RESET_PARAMS);
	sr = SQLFreeStmt(stmt, SQL_CLOSE);
	//IMAGE locator
	sr = SQLBindParameter(stmt, 1, SQL_PARAM_INPUT, SQL_C_BINARY, SQL_BINARY, l4LOB, 0, c4LOB, l4LOB, &l4LOB);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLExecDirect(stmt, createIMAGE_LOC_SQL, SQL_NTS);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLBindCol(stmt, 1, SQL_C_IMAGE_LOCATOR, c4LOC, l4LOC, &l4LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLFetch(stmt);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLFreeStmt(stmt, SQL_UNBIND);
	sr = SQLFreeStmt(stmt, SQL_RESET_PARAMS);
	sr = SQLFreeStmt(stmt, SQL_CLOSE);
	//Now we will insert data into a table using LOB locators
	sr = SQLBindParameter(stmt, 1, SQL_PARAM_INPUT, SQL_C_LONG, SQL_INTEGER, l1, 0, &c1, l1, &l1);
	printError(sr, SQL_HANDLE_STMT, stmt);
	//Bind the locators
	sr = SQLBindParameter(stmt, 2, SQL_PARAM_INPUT, SQL_C_TEXT_LOCATOR, SQL_TEXT_LOCATOR, l2LOC, 0, c2LOC, l2LOC, &l2LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLBindParameter(stmt, 3, SQL_PARAM_INPUT, SQL_C_UNITEXT_LOCATOR, SQL_UNITEXT_LOCATOR, l3LOC, 0, c3LOC, l3LOC, &l3LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLBindParameter(stmt, 4, SQL_PARAM_INPUT, SQL_C_IMAGE_LOCATOR, SQL_IMAGE_LOCATOR, l4LOC, 0, c4LOC, l4LOC, &l4LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	//Execute the insert
	sr = SQLExecDirect(stmt, insertStmt, SQL_NTS);
	printError(sr, SQL_HANDLE_STMT, stmt);
	//Cleanup
	sr = SQLFreeStmt(stmt, SQL_UNBIND);
	sr = SQLFreeStmt(stmt, SQL_RESET_PARAMS);
	sr = SQLFreeStmt(stmt, SQL_CLOSE);
	// Cleanup the statement handle
	sr = SQLFreeStmt(stmt, SQL_UNBIND);
	sr = SQLFreeStmt(stmt, SQL_RESET_PARAMS);
	sr = SQLFreeStmt(stmt, SQL_CLOSE);
	sr = SQLEndTran(SQL_HANDLE_DBC, dbc, SQL_COMMIT);
	sr = SQLSetConnectAttr(dbc, SQL_ATTR_AUTOCOMMIT, (SQLPOINTER)SQL_AUTOCOMMIT_ON, 0);
}
void Substring(SQLHDBC dbc, SQLHSTMT stmt)
{
	SQLRETURN sr;
	sr = SQLSetConnectAttr(dbc, SQL_ATTR_AUTOCOMMIT, (SQLPOINTER)SQL_AUTOCOMMIT_OFF, 0);
	//Get a locator from the server
	unsigned char c2LOC[SQL_LOCATOR_SIZE];
	SQLLEN l2LOC = sizeof(c2LOC);
	SQLCHAR c2LOB[512];
	SQLLEN l2LOB = 512;
	unsigned char c3LOC[SQL_LOCATOR_SIZE];
	SQLLEN l3LOC = sizeof(c3LOC);
	SQLWCHAR c3LOB[512];
	SQLLEN l3LOB = 512;
	unsigned char c4LOC[SQL_LOCATOR_SIZE];
	SQLLEN l4LOC = sizeof(c4LOC);
	SQLCHAR c4LOB[512];
	SQLLEN l4LOB = 512;
	int id = 0;
	int c1 = 1;
	SQLLEN l1 = sizeof(int);
	SQLLEN idLen = sizeof(int);
	sr = SQLBindParameter(stmt, 1, SQL_PARAM_INPUT, SQL_C_LONG, SQL_INTEGER, idLen, 0, &id, idLen, &idLen);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLExecDirect(stmt, selectCOL_SQL, SQL_NTS);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLFetch(stmt);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLGetData(stmt, 1, SQL_C_TEXT_LOCATOR, c2LOC, l2LOC, &l2LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLGetData(stmt, 2, SQL_C_TEXT_LOCATOR, c3LOC, l3LOC, &l3LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLGetData(stmt, 3, SQL_C_TEXT_LOCATOR, c4LOC, l4LOC, &l4LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLFreeStmt(stmt, SQL_UNBIND);
	sr = SQLFreeStmt(stmt, SQL_RESET_PARAMS);
	sr = SQLFreeStmt(stmt, SQL_CLOSE);
	int start = 10;
	SQLLEN lStart = sizeof(int);
	int end = 100;
	SQLLEN lEnd = sizeof(int);
	//Substring TEXT
	sr = SQLBindParameter(stmt, 1, SQL_PARAM_INPUT, SQL_C_TEXT_LOCATOR, SQL_TEXT_LOCATOR, l2LOC, 0, c2LOC, l2LOC, &l2LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLBindParameter(stmt, 2, SQL_PARAM_INPUT, SQL_C_LONG, SQL_INTEGER, lStart, 0, &start, lStart, &lStart);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLBindParameter(stmt, 3, SQL_PARAM_INPUT, SQL_C_LONG, SQL_INTEGER, lEnd, 0, &end, lEnd, &lEnd);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLExecDirect(stmt, substringTEXT_SQL, SQL_NTS);
	printError(sr, SQL_HANDLE_STMT, stmt);
	//Since a new locator is returned we need to do a fetch
	sr = SQLBindCol(stmt, 1, SQL_C_CHAR, c2LOB, l2LOB, &l2LOB);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLFetch(stmt);
	printError(sr, SQL_HANDLE_STMT, stmt);
	//Substring TEXT Cleanup
	sr = SQLFreeStmt(stmt, SQL_UNBIND);
	sr = SQLFreeStmt(stmt, SQL_RESET_PARAMS);
	sr = SQLFreeStmt(stmt, SQL_CLOSE);
	//Substring UNITEXT
	sr = SQLBindParameter(stmt, 1, SQL_PARAM_INPUT, SQL_C_UNITEXT_LOCATOR, SQL_UNITEXT_LOCATOR, l3LOC, 0, c3LOC, l3LOC, &l3LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLBindParameter(stmt, 2, SQL_PARAM_INPUT, SQL_C_LONG, SQL_INTEGER, lStart, 0, &start, lStart, &lStart);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLBindParameter(stmt, 3, SQL_PARAM_INPUT, SQL_C_LONG, SQL_INTEGER, lEnd, 0, &end, lEnd, &lEnd);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLExecDirect(stmt, substringUNITEXT_SQL, SQL_NTS);
	printError(sr, SQL_HANDLE_STMT, stmt);
	//Since a new locator is returned we need to do a fetch
	sr = SQLBindCol(stmt, 1, SQL_C_WCHAR, c3LOB, l3LOB, &l3LOB);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLFetch(stmt);
	printError(sr, SQL_HANDLE_STMT, stmt);
	//Substring UNITEXT Cleanup
	sr = SQLFreeStmt(stmt, SQL_UNBIND);
	sr = SQLFreeStmt(stmt, SQL_RESET_PARAMS);
	sr = SQLFreeStmt(stmt, SQL_CLOSE);
	//Substring IMAGE
	sr = SQLBindParameter(stmt, 1, SQL_PARAM_INPUT, SQL_C_IMAGE_LOCATOR, SQL_IMAGE_LOCATOR, l4LOC, 0, c4LOC, l4LOC, &l4LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLBindParameter(stmt, 2, SQL_PARAM_INPUT, SQL_C_LONG, SQL_INTEGER, lStart, 0, &start, lStart, &lStart);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLBindParameter(stmt, 3, SQL_PARAM_INPUT, SQL_C_LONG, SQL_INTEGER, lEnd, 0, &end, lEnd, &lEnd);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLExecDirect(stmt, substringIMAGE_SQL, SQL_NTS);
	printError(sr, SQL_HANDLE_STMT, stmt);
	//Since a new locator is returned we need to do a fetch
	sr = SQLBindCol(stmt, 1, SQL_C_BINARY, c4LOB, l4LOB, &l4LOB);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLFetch(stmt);
	printError(sr, SQL_HANDLE_STMT, stmt);
	//Substring IMAGE Cleanup
	sr = SQLFreeStmt(stmt, SQL_UNBIND);
	sr = SQLFreeStmt(stmt, SQL_RESET_PARAMS);
	sr = SQLFreeStmt(stmt, SQL_CLOSE);
	//c2LOB is now the value "mistake is to consider \"iterative\" and \"incremental\" as synonyms, which they are not. In software/sy"
	//c3LOB is now the value "mistake is to consider \"iterative\" and \"incremental\" as synonyms, which they are not. In software/sy"
	//c4LOB is now the value starting at 0x09 and continuing to 0x6C
	//Insert to save the values
	sr = SQLBindParameter(stmt, 1, SQL_PARAM_INPUT, SQL_C_LONG, SQL_INTEGER, l1, 0, &c1, l1, &l1);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLBindParameter(stmt, 2, SQL_PARAM_INPUT, SQL_C_CHAR, SQL_VARCHAR, l2LOB, 0, c2LOB, l2LOB, &l2LOB);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLBindParameter(stmt, 3, SQL_PARAM_INPUT, SQL_C_WCHAR, SQL_WVARCHAR, l3LOB, 0, c3LOB, l3LOB, &l3LOB);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLBindParameter(stmt, 4, SQL_PARAM_INPUT, SQL_C_BINARY, SQL_VARBINARY, l4LOB, 0, c4LOB, l4LOB, &l4LOB);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLExecDirect(stmt, insertStmt, SQL_NTS);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLFreeStmt(stmt, SQL_UNBIND);
	sr = SQLFreeStmt(stmt, SQL_RESET_PARAMS);
	sr = SQLFreeStmt(stmt, SQL_CLOSE);
	sr = SQLEndTran(SQL_HANDLE_DBC, dbc, SQL_COMMIT);
	sr = SQLSetConnectAttr(dbc, SQL_ATTR_AUTOCOMMIT, (SQLPOINTER)SQL_AUTOCOMMIT_ON, 0);
}
void Setdata(SQLHDBC dbc, SQLHSTMT stmt)
{
	SQLRETURN sr;
	sr = SQLSetConnectAttr(dbc, SQL_ATTR_AUTOCOMMIT, (SQLPOINTER)SQL_AUTOCOMMIT_OFF, 0);
	//Get a locator from the server
	unsigned char c2LOC[SQL_LOCATOR_SIZE];
	SQLLEN l2LOC = sizeof(c2LOC);
	unsigned char c3LOC[SQL_LOCATOR_SIZE];
	SQLLEN l3LOC = sizeof(c3LOC);
	unsigned char c4LOC[SQL_LOCATOR_SIZE];
	SQLLEN l4LOC = sizeof(c4LOC);
	int id = 1;
	int c1 = 2;
	SQLLEN l1 = sizeof(int);
	SQLLEN idLen = sizeof(int);
	sr = SQLBindParameter(stmt, 1, SQL_PARAM_INPUT, SQL_C_LONG, SQL_INTEGER, idLen, 0, &id, idLen, &idLen);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLExecDirect(stmt, selectCOL_SQL, SQL_NTS);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLFetch(stmt);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLGetData(stmt, 1, SQL_C_TEXT_LOCATOR, c2LOC, l2LOC, &l2LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLGetData(stmt, 2, SQL_C_TEXT_LOCATOR, c3LOC, l3LOC, &l3LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLGetData(stmt, 3, SQL_C_TEXT_LOCATOR, c4LOC, l4LOC, &l4LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLFreeStmt(stmt, SQL_UNBIND);
	sr = SQLFreeStmt(stmt, SQL_RESET_PARAMS);
	sr = SQLFreeStmt(stmt, SQL_CLOSE);
	//Setdata with values
	int charsReplaced = 0;
	SQLLEN CRLength = sizeof(int);
	int index = 10;
	SQLLEN lIndex = sizeof(int);
	SQLCHAR cSubstr[10] = "Alpha";
	SQLLEN lSubstr = 5;
	//SetData TEXT
	sr = SQLBindParameter(stmt, 1, SQL_PARAM_INPUT, SQL_C_TEXT_LOCATOR, SQL_TEXT_LOCATOR, l2LOC, 0, c2LOC, l2LOC, &l2LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLBindParameter(stmt, 2, SQL_PARAM_INPUT, SQL_C_LONG, SQL_INTEGER, lIndex, 0, &index, lIndex, &lIndex);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLBindParameter(stmt, 3, SQL_PARAM_INPUT, SQL_C_CHAR, SQL_CHAR, lSubstr, 0, &cSubstr, lSubstr, &lSubstr);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLBindParameter(stmt, 4, SQL_PARAM_OUTPUT, SQL_C_LONG, SQL_INTEGER, CRLength, 0, &charsReplaced, CRLength, &CRLength);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLExecDirect(stmt, setdataTEXT_SQL, SQL_NTS);
	printError(sr, SQL_HANDLE_STMT, stmt);
	//SetData TEXT Cleanup
	sr = SQLFreeStmt(stmt, SQL_UNBIND);
	sr = SQLFreeStmt(stmt, SQL_RESET_PARAMS);
	sr = SQLFreeStmt(stmt, SQL_CLOSE);
	//SetData UNITEXT
	SQLWCHAR uSubstr[10];
	memcpy(uSubstr, L"Alpha", 10 * sizeof(SQLWCHAR));
	lSubstr = 10;
	sr = SQLBindParameter(stmt, 1, SQL_PARAM_INPUT, SQL_C_UNITEXT_LOCATOR, SQL_UNITEXT_LOCATOR, l3LOC, 0, c3LOC, l3LOC, &l3LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLBindParameter(stmt, 2, SQL_PARAM_INPUT, SQL_C_LONG, SQL_INTEGER, lIndex, 0, &index, lIndex, &lIndex);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLBindParameter(stmt, 3, SQL_PARAM_INPUT, SQL_C_WCHAR, SQL_WCHAR, lSubstr, 0, &uSubstr, lSubstr, &lSubstr);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLBindParameter(stmt, 4, SQL_PARAM_OUTPUT, SQL_C_LONG, SQL_INTEGER, CRLength, 0, &charsReplaced, CRLength, &CRLength);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLExecDirect(stmt, setdataUNITEXT_SQL, SQL_NTS);
	printError(sr, SQL_HANDLE_STMT, stmt);
	//SetData UNITEXT Cleanup
	sr = SQLFreeStmt(stmt, SQL_UNBIND);
	sr = SQLFreeStmt(stmt, SQL_RESET_PARAMS);
	sr = SQLFreeStmt(stmt, SQL_CLOSE);
	//SetData IMAGE
	unsigned char iSubstr[5] = {0x05, 0x04, 0x03, 0x02, 0x01};
	lSubstr = 5;
	sr = SQLBindParameter(stmt, 1, SQL_PARAM_INPUT, SQL_C_IMAGE_LOCATOR, SQL_IMAGE_LOCATOR, l4LOC, 0, c4LOC, l4LOC, &l4LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLBindParameter(stmt, 2, SQL_PARAM_INPUT, SQL_C_LONG, SQL_INTEGER, lIndex, 0, &index, lIndex, &lIndex);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLBindParameter(stmt, 3, SQL_PARAM_INPUT, SQL_C_BINARY, SQL_BINARY, lSubstr, 0, &iSubstr, lSubstr, &lSubstr);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLBindParameter(stmt, 4, SQL_PARAM_OUTPUT, SQL_C_LONG, SQL_INTEGER, CRLength, 0, &charsReplaced, CRLength, &CRLength);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLExecDirect(stmt, setdataIMAGE_SQL, SQL_NTS);
	printError(sr, SQL_HANDLE_STMT, stmt);
	//SetData IMAGE Cleanup
	sr = SQLFreeStmt(stmt, SQL_UNBIND);
	sr = SQLFreeStmt(stmt, SQL_RESET_PARAMS);
	sr = SQLFreeStmt(stmt, SQL_CLOSE);
	//c2LOC now references the value "mistake iAlphaconsider \"iterative\" and \"incremental\" as synonyms, which they are not. In software/sy"
	//c3LOC now references the value "mistake iAlphaconsider \"iterative\" and \"incremental\" as synonyms, which they are not. In software/sy"
	//c4LOC now references the value 0x09 to 0x11, 0x05 to 0x01, 0x17 to 0x6C
	//Insert to save the values
	sr = SQLBindParameter(stmt, 1, SQL_PARAM_INPUT, SQL_C_LONG, SQL_INTEGER, l1, 0, &c1, l1, &l1);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLBindParameter(stmt, 2, SQL_PARAM_INPUT, SQL_C_TEXT_LOCATOR, SQL_TEXT_LOCATOR, l2LOC, 0, c2LOC, l2LOC, &l2LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLBindParameter(stmt, 3, SQL_PARAM_INPUT, SQL_C_UNITEXT_LOCATOR, SQL_UNITEXT_LOCATOR, l3LOC, 0, c3LOC, l3LOC, &l3LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLBindParameter(stmt, 4, SQL_PARAM_INPUT, SQL_C_IMAGE_LOCATOR, SQL_IMAGE_LOCATOR, l4LOC, 0, c4LOC, l4LOC, &l4LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLExecDirect(stmt, insertStmt, SQL_NTS);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLFreeStmt(stmt, SQL_UNBIND);
	sr = SQLFreeStmt(stmt, SQL_RESET_PARAMS);
	sr = SQLFreeStmt(stmt, SQL_CLOSE);
	sr = SQLEndTran(SQL_HANDLE_DBC, dbc, SQL_COMMIT);
	sr = SQLSetConnectAttr(dbc, SQL_ATTR_AUTOCOMMIT, (SQLPOINTER)SQL_AUTOCOMMIT_ON, 0);
}

void Setdata_append(SQLHDBC dbc, SQLHSTMT stmt)
{
	SQLRETURN sr;
	sr = SQLSetConnectAttr(dbc, SQL_ATTR_AUTOCOMMIT, (SQLPOINTER)SQL_AUTOCOMMIT_OFF, 0);
	//Get a locator from the server
	unsigned char c2LOC[SQL_LOCATOR_SIZE];
	SQLLEN l2LOC = sizeof(c2LOC);
	unsigned char c3LOC[SQL_LOCATOR_SIZE];
	SQLLEN l3LOC = sizeof(c3LOC);
	unsigned char c4LOC[SQL_LOCATOR_SIZE];
	SQLLEN l4LOC = sizeof(c4LOC);
	int id = 2;
	int c1 = 3;
	SQLLEN l1 = sizeof(int);
	SQLLEN idLen = sizeof(int);
	int charsReplaced = 0;
	SQLLEN CRLength = sizeof(int);
	sr = SQLBindParameter(stmt, 1, SQL_PARAM_INPUT, SQL_C_LONG, SQL_INTEGER, idLen, 0, &id, idLen, &idLen);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLExecDirect(stmt, selectCOL_SQL, SQL_NTS);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLFetch(stmt);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLGetData(stmt, 1, SQL_C_TEXT_LOCATOR, c2LOC, l2LOC, &l2LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLGetData(stmt, 2, SQL_C_TEXT_LOCATOR, c3LOC, l3LOC, &l3LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLGetData(stmt, 3, SQL_C_TEXT_LOCATOR, c4LOC, l4LOC, &l4LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLFreeStmt(stmt, SQL_UNBIND);
	sr = SQLFreeStmt(stmt, SQL_RESET_PARAMS);
	sr = SQLFreeStmt(stmt, SQL_CLOSE);
	int index = 10;
	SQLLEN lIndex = sizeof(int);
	//Setdata with locators/ Append
	//To append you call setdata and specify the length of the data + 1
	//There will ba an example of how to get the length of the data pointed to by a locator later
	index = 101;
	lIndex = sizeof(int);
	//SetData TEXT setup
	unsigned char tmpLOC[SQL_LOCATOR_SIZE];
	SQLLEN tmpLOCLen = SQL_LOCATOR_SIZE;
	SQLCHAR appendDataT[16] = "END";
	SQLLEN adTLen = SQL_NTS;
	sr = SQLBindParameter(stmt, 1, SQL_PARAM_INPUT, SQL_C_CHAR, SQL_CHAR, 16, 0, appendDataT, 16, &adTLen);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLExecDirect(stmt, createTEXT_LOC_SQL, SQL_NTS);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLBindCol(stmt, 1, SQL_C_TEXT_LOCATOR, tmpLOC, tmpLOCLen, &tmpLOCLen);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLFetch(stmt);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLFreeStmt(stmt, SQL_UNBIND);
	sr = SQLFreeStmt(stmt, SQL_CLOSE);
	//SetData TEXT
	sr = SQLBindParameter(stmt, 1, SQL_PARAM_INPUT, SQL_C_TEXT_LOCATOR, SQL_TEXT_LOCATOR, l2LOC, 0, c2LOC, l2LOC, &l2LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLBindParameter(stmt, 2, SQL_PARAM_INPUT, SQL_C_LONG, SQL_INTEGER, lIndex, 0, &index, lIndex, &lIndex);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLBindParameter(stmt, 3, SQL_PARAM_INPUT, SQL_C_TEXT_LOCATOR, SQL_TEXT_LOCATOR, tmpLOCLen, 0, tmpLOC, tmpLOCLen, &tmpLOCLen);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLBindParameter(stmt, 4, SQL_PARAM_OUTPUT, SQL_C_LONG, SQL_INTEGER, CRLength, 0, &charsReplaced, CRLength, &CRLength);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLExecDirect(stmt, setdataTEXT_LOC_SQL, SQL_NTS);
	printError(sr, SQL_HANDLE_STMT, stmt);
	//SetData TEXT Cleanup
	sr = SQLFreeStmt(stmt, SQL_UNBIND);
	sr = SQLFreeStmt(stmt, SQL_RESET_PARAMS);
	sr = SQLFreeStmt(stmt, SQL_CLOSE);
	//Setdata UNITEXT setup
	SQLWCHAR appendDataU[16];
	memcpy(appendDataU, L"END", 16 * sizeof(SQLWCHAR));
	SQLLEN adULen = SQL_NTS;
	sr = SQLBindParameter(stmt, 1, SQL_PARAM_INPUT, SQL_C_WCHAR, SQL_WCHAR, 16, 0, appendDataU, 16, &adULen);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLExecDirect(stmt, createUNITEXT_LOC_SQL, SQL_NTS);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLBindCol(stmt, 1, SQL_C_UNITEXT_LOCATOR, tmpLOC, tmpLOCLen, &tmpLOCLen);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLFetch(stmt);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLFreeStmt(stmt, SQL_UNBIND);
	sr = SQLFreeStmt(stmt, SQL_CLOSE);
	//SetData UNITEXT
	sr = SQLBindParameter(stmt, 1, SQL_PARAM_INPUT, SQL_C_UNITEXT_LOCATOR, SQL_UNITEXT_LOCATOR, l3LOC, 0, c3LOC, l3LOC, &l3LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLBindParameter(stmt, 2, SQL_PARAM_INPUT, SQL_C_LONG, SQL_INTEGER, lIndex, 0, &index, lIndex, &lIndex);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLBindParameter(stmt, 3, SQL_PARAM_INPUT, SQL_C_UNITEXT_LOCATOR, SQL_UNITEXT_LOCATOR, tmpLOCLen, 0, tmpLOC, tmpLOCLen, &tmpLOCLen);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLBindParameter(stmt, 4, SQL_PARAM_OUTPUT, SQL_C_LONG, SQL_INTEGER, CRLength, 0, &charsReplaced, CRLength, &CRLength);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLExecDirect(stmt, setdataUNITEXT_LOC_SQL, SQL_NTS);
	printError(sr, SQL_HANDLE_STMT, stmt);
	//SetData UNITEXT Cleanup
	sr = SQLFreeStmt(stmt, SQL_UNBIND);
	sr = SQLFreeStmt(stmt, SQL_RESET_PARAMS);
	sr = SQLFreeStmt(stmt, SQL_CLOSE);
	//Setdata IMAGE setup
	unsigned char appendDataB[16] = {0x03, 0x04, 0x17};
	SQLLEN adBLen = 3;
	sr = SQLBindParameter(stmt, 1, SQL_PARAM_INPUT, SQL_C_CHAR, SQL_CHAR, 16, 0, appendDataB, 16, &adBLen);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLExecDirect(stmt, createIMAGE_LOC_SQL, SQL_NTS);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLBindCol(stmt, 1, SQL_C_IMAGE_LOCATOR, tmpLOC, tmpLOCLen, &tmpLOCLen);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLFetch(stmt);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLFreeStmt(stmt, SQL_UNBIND);
	sr = SQLFreeStmt(stmt, SQL_CLOSE);
	//SetData IMAGE
	sr = SQLBindParameter(stmt, 1, SQL_PARAM_INPUT, SQL_C_IMAGE_LOCATOR, SQL_IMAGE_LOCATOR, l4LOC, 0, c4LOC, l4LOC, &l4LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLBindParameter(stmt, 2, SQL_PARAM_INPUT, SQL_C_LONG, SQL_INTEGER, lIndex, 0, &index, lIndex, &lIndex);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLBindParameter(stmt, 3, SQL_PARAM_INPUT, SQL_C_IMAGE_LOCATOR, SQL_IMAGE_LOCATOR, tmpLOCLen, 0, tmpLOC, tmpLOCLen, &tmpLOCLen);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLBindParameter(stmt, 4, SQL_PARAM_OUTPUT, SQL_C_LONG, SQL_INTEGER, CRLength, 0, &charsReplaced, CRLength, &CRLength);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLExecDirect(stmt, setdataIMAGE_LOC_SQL, SQL_NTS);
	printError(sr, SQL_HANDLE_STMT, stmt);
	//SetData IMAGE Cleanup
	sr = SQLFreeStmt(stmt, SQL_UNBIND);
	sr = SQLFreeStmt(stmt, SQL_RESET_PARAMS);
	sr = SQLFreeStmt(stmt, SQL_CLOSE);
	//c2LOC now references the value "mistake iAlphaconsider \"iterative\" and \"incremental\" as synonyms, which they are not. In software/syEND"
	//c3LOC now references the value "mistake iAlphaconsider \"iterative\" and \"incremental\" as synonyms, which they are not. In software/syEND"
	//c4LOC now references the value 0x09 to 0x11, 0x05 to 0x01, 0x17 to 0x6E, 0x030417
	//Insert to save the values
	sr = SQLBindParameter(stmt, 1, SQL_PARAM_INPUT, SQL_C_LONG, SQL_INTEGER, l1, 0, &c1, l1, &l1);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLBindParameter(stmt, 2, SQL_PARAM_INPUT, SQL_C_TEXT_LOCATOR, SQL_TEXT_LOCATOR, l2LOC, 0, c2LOC, l2LOC, &l2LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLBindParameter(stmt, 3, SQL_PARAM_INPUT, SQL_C_UNITEXT_LOCATOR, SQL_UNITEXT_LOCATOR, l3LOC, 0, c3LOC, l3LOC, &l3LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLBindParameter(stmt, 4, SQL_PARAM_INPUT, SQL_C_IMAGE_LOCATOR, SQL_IMAGE_LOCATOR, l4LOC, 0, c4LOC, l4LOC, &l4LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLExecDirect(stmt, insertStmt, SQL_NTS);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLFreeStmt(stmt, SQL_UNBIND);
	sr = SQLFreeStmt(stmt, SQL_RESET_PARAMS);
	sr = SQLFreeStmt(stmt, SQL_CLOSE);
	sr = SQLEndTran(SQL_HANDLE_DBC, dbc, SQL_COMMIT);
	sr = SQLSetConnectAttr(dbc, SQL_ATTR_AUTOCOMMIT, (SQLPOINTER)SQL_AUTOCOMMIT_ON, 0);
}

void Truncate(SQLHDBC dbc, SQLHSTMT stmt)
{
	SQLRETURN sr;
	sr = SQLSetConnectAttr(dbc, SQL_ATTR_AUTOCOMMIT, (SQLPOINTER)SQL_AUTOCOMMIT_OFF, 0);
	//Get a locator from the server
	unsigned char c2LOC[SQL_LOCATOR_SIZE];
	SQLLEN l2LOC = sizeof(c2LOC);
	unsigned char c3LOC[SQL_LOCATOR_SIZE];
	SQLLEN l3LOC = sizeof(c3LOC);
	unsigned char c4LOC[SQL_LOCATOR_SIZE];
	SQLLEN l4LOC = sizeof(c4LOC);
	int id = 3;
	int c1 = 4;
	SQLLEN l1 = sizeof(int);
	SQLLEN idLen = sizeof(int);
	sr = SQLBindParameter(stmt, 1, SQL_PARAM_INPUT, SQL_C_LONG, SQL_INTEGER, idLen, 0, &id, idLen, &idLen);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLExecDirect(stmt, selectCOL_SQL, SQL_NTS);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLFetch(stmt);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLGetData(stmt, 1, SQL_C_TEXT_LOCATOR, c2LOC, l2LOC, &l2LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLGetData(stmt, 2, SQL_C_TEXT_LOCATOR, c3LOC, l3LOC, &l3LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLGetData(stmt, 3, SQL_C_TEXT_LOCATOR, c4LOC, l4LOC, &l4LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLFreeStmt(stmt, SQL_UNBIND);
	sr = SQLFreeStmt(stmt, SQL_RESET_PARAMS);
	sr = SQLFreeStmt(stmt, SQL_CLOSE);
	//Truncate LOB
	int length = 50;
	SQLLEN lLength = sizeof(int);
	//Truncate TEXT
	sr = SQLBindParameter(stmt, 1, SQL_PARAM_INPUT, SQL_C_TEXT_LOCATOR, SQL_TEXT_LOCATOR, l2LOC, 0, c2LOC, l2LOC, &l2LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLBindParameter(stmt, 2, SQL_PARAM_INPUT, SQL_C_LONG, SQL_INTEGER, lLength, 0, &length, lLength, &lLength);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLExecDirect(stmt, truncateLOB_SQL, SQL_NTS);
	printError(sr, SQL_HANDLE_STMT, stmt);
	//Truncate TEXT Cleanup
	sr = SQLFreeStmt(stmt, SQL_UNBIND);
	sr = SQLFreeStmt(stmt, SQL_RESET_PARAMS);
	sr = SQLFreeStmt(stmt, SQL_CLOSE);
	//Truncate UNITEXT
	sr = SQLBindParameter(stmt, 1, SQL_PARAM_INPUT, SQL_C_UNITEXT_LOCATOR, SQL_UNITEXT_LOCATOR, l3LOC, 0, c3LOC, l3LOC, &l3LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLBindParameter(stmt, 2, SQL_PARAM_INPUT, SQL_C_LONG, SQL_INTEGER, lLength, 0, &length, lLength, &lLength);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLExecDirect(stmt, truncateLOB_SQL, SQL_NTS);
	printError(sr, SQL_HANDLE_STMT, stmt);
	//Truncate UNITEXT Cleanup
	sr = SQLFreeStmt(stmt, SQL_UNBIND);
	sr = SQLFreeStmt(stmt, SQL_RESET_PARAMS);
	sr = SQLFreeStmt(stmt, SQL_CLOSE);
	//Truncate IMAGE
	sr = SQLBindParameter(stmt, 1, SQL_PARAM_INPUT, SQL_C_IMAGE_LOCATOR, SQL_IMAGE_LOCATOR, l4LOC, 0, c4LOC, l4LOC, &l4LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLBindParameter(stmt, 2, SQL_PARAM_INPUT, SQL_C_LONG, SQL_INTEGER, lLength, 0, &length, lLength, &lLength);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLExecDirect(stmt, truncateLOB_SQL, SQL_NTS);
	printError(sr, SQL_HANDLE_STMT, stmt);
	//Truncate IMAGE Cleanup
	sr = SQLFreeStmt(stmt, SQL_UNBIND);
	sr = SQLFreeStmt(stmt, SQL_RESET_PARAMS);
	sr = SQLFreeStmt(stmt, SQL_CLOSE);
	//c2LOC now references the value "mistake iAlphaconsider \"iterative\" and \"incrementa"
	//c3LOC now references the value "mistake iAlphaconsider \"iterative\" and \"incrementa"
	//c4LOC now references the value 0x09 to 0x11, 0x05 to 0x01, 0x17 to 0x3A
	//Insert to save the values
	sr = SQLBindParameter(stmt, 1, SQL_PARAM_INPUT, SQL_C_LONG, SQL_INTEGER, l1, 0, &c1, l1, &l1);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLBindParameter(stmt, 2, SQL_PARAM_INPUT, SQL_C_TEXT_LOCATOR, SQL_TEXT_LOCATOR, l2LOC, 0, c2LOC, l2LOC, &l2LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLBindParameter(stmt, 3, SQL_PARAM_INPUT, SQL_C_UNITEXT_LOCATOR, SQL_UNITEXT_LOCATOR, l3LOC, 0, c3LOC, l3LOC, &l3LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLBindParameter(stmt, 4, SQL_PARAM_INPUT, SQL_C_IMAGE_LOCATOR, SQL_IMAGE_LOCATOR, l4LOC, 0, c4LOC, l4LOC, &l4LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLExecDirect(stmt, insertStmt, SQL_NTS);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLFreeStmt(stmt, SQL_UNBIND);
	sr = SQLFreeStmt(stmt, SQL_RESET_PARAMS);
	sr = SQLFreeStmt(stmt, SQL_CLOSE);
	sr = SQLEndTran(SQL_HANDLE_DBC, dbc, SQL_COMMIT);
	sr = SQLSetConnectAttr(dbc, SQL_ATTR_AUTOCOMMIT, (SQLPOINTER)SQL_AUTOCOMMIT_ON, 0);
}

void ReturnLOB(SQLHDBC dbc, SQLHSTMT stmt)
{
	SQLRETURN sr;
	sr = SQLSetConnectAttr(dbc, SQL_ATTR_AUTOCOMMIT, (SQLPOINTER)SQL_AUTOCOMMIT_OFF, 0);
	//Get a locator from the server
	SQLCHAR c2LOB[2401];
	SQLLEN l2LOB = sizeof(c2LOB);
	SQLWCHAR c3LOB[2401];
	SQLLEN l3LOB = sizeof(c3LOB);
	unsigned char c4LOB[2401];
	SQLLEN l4LOB = sizeof(c4LOB);
	unsigned char c2LOC[SQL_LOCATOR_SIZE];
	SQLLEN l2LOC = sizeof(c2LOC);
	unsigned char c3LOC[SQL_LOCATOR_SIZE];
	SQLLEN l3LOC = sizeof(c3LOC);
	unsigned char c4LOC[SQL_LOCATOR_SIZE];
	SQLLEN l4LOC = sizeof(c4LOC);
	int id = 4;
	SQLLEN l1 = sizeof(int);
	SQLLEN idLen = sizeof(int);
	sr = SQLBindParameter(stmt, 1, SQL_PARAM_INPUT, SQL_C_LONG, SQL_INTEGER, idLen, 0, &id, idLen, &idLen);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLExecDirect(stmt, selectCOL_SQL, SQL_NTS);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLFetch(stmt);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLGetData(stmt, 1, SQL_C_TEXT_LOCATOR, c2LOC, l2LOC, &l2LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLGetData(stmt, 2, SQL_C_TEXT_LOCATOR, c3LOC, l3LOC, &l3LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLGetData(stmt, 3, SQL_C_TEXT_LOCATOR, c4LOC, l4LOC, &l4LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLFreeStmt(stmt, SQL_UNBIND);
	sr = SQLFreeStmt(stmt, SQL_RESET_PARAMS);
	sr = SQLFreeStmt(stmt, SQL_CLOSE);
	//Return LOB
	//Return TEXT
	sr = SQLBindParameter(stmt, 1, SQL_PARAM_INPUT, SQL_C_TEXT_LOCATOR, SQL_TEXT_LOCATOR, l2LOC, 0, c2LOC, l2LOC, &l2LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLExecDirect(stmt, TLTTSQL, SQL_NTS);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLFetch(stmt);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLGetData(stmt, 1, SQL_C_CHAR, c2LOB, l2LOB, &l2LOB);
	printError(sr, SQL_HANDLE_STMT, stmt);
	//Return TEXT Cleanup
	sr = SQLFreeStmt(stmt, SQL_UNBIND);
	sr = SQLFreeStmt(stmt, SQL_RESET_PARAMS);
	sr = SQLFreeStmt(stmt, SQL_CLOSE);
	//Return UNITEXT
	sr = SQLBindParameter(stmt, 1, SQL_PARAM_INPUT, SQL_C_UNITEXT_LOCATOR, SQL_UNITEXT_LOCATOR, l3LOC, 0, c3LOC, l3LOC, &l3LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLExecDirect(stmt, UTLTUTSQL, SQL_NTS);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLFetch(stmt);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLGetData(stmt, 1, SQL_C_WCHAR, c3LOB, l3LOB, &l3LOB);
	printError(sr, SQL_HANDLE_STMT, stmt);
	//Return UNITEXT Cleanup
	sr = SQLFreeStmt(stmt, SQL_UNBIND);
	sr = SQLFreeStmt(stmt, SQL_RESET_PARAMS);
	sr = SQLFreeStmt(stmt, SQL_CLOSE);
	//Return IMAGE
	sr = SQLBindParameter(stmt, 1, SQL_PARAM_INPUT, SQL_C_IMAGE_LOCATOR, SQL_IMAGE_LOCATOR, l4LOC, 0, c4LOC, l4LOC, &l4LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLExecDirect(stmt, ILTISQL, SQL_NTS);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLFetch(stmt);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLGetData(stmt, 1, SQL_C_BINARY, c4LOB, l4LOB, &l4LOB);
	printError(sr, SQL_HANDLE_STMT, stmt);
	//Return IMAGE Cleanup
	sr = SQLFreeStmt(stmt, SQL_UNBIND);
	sr = SQLFreeStmt(stmt, SQL_RESET_PARAMS);
	sr = SQLFreeStmt(stmt, SQL_CLOSE);
	//c2LOB now references the value "mistake iAlphaconsider \"iterative\" and \"incrementa"
	//c3LOB now references the value "mistake iAlphaconsider \"iterative\" and \"incrementa"
	//c4LOB now references the value 0x0A to 0x12, 0x05 to 0x01, 0x18 to 0x32
	sr = SQLEndTran(SQL_HANDLE_DBC, dbc, SQL_COMMIT);
	sr = SQLSetConnectAttr(dbc, SQL_ATTR_AUTOCOMMIT, (SQLPOINTER)SQL_AUTOCOMMIT_ON, 0);
}

void CharLength(SQLHDBC dbc, SQLHSTMT stmt)
{
	SQLRETURN sr;
	sr = SQLSetConnectAttr(dbc, SQL_ATTR_AUTOCOMMIT, (SQLPOINTER)SQL_AUTOCOMMIT_OFF, 0);
	//Get a locator from the server
	unsigned char c2LOC[SQL_LOCATOR_SIZE];
	SQLLEN l2LOC = sizeof(c2LOC);
	unsigned char c3LOC[SQL_LOCATOR_SIZE];
	SQLLEN l3LOC = sizeof(c3LOC);
	unsigned char c4LOC[SQL_LOCATOR_SIZE];
	SQLLEN l4LOC = sizeof(c4LOC);
	int id = 3;
	int c1 = 4;
	SQLLEN l1 = sizeof(int);
	SQLLEN idLen = sizeof(int);
	sr = SQLBindParameter(stmt, 1, SQL_PARAM_INPUT, SQL_C_LONG, SQL_INTEGER, idLen, 0, &id, idLen, &idLen);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLExecDirect(stmt, selectCOL_SQL, SQL_NTS);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLFetch(stmt);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLGetData(stmt, 1, SQL_C_TEXT_LOCATOR, c2LOC, l2LOC, &l2LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLGetData(stmt, 2, SQL_C_TEXT_LOCATOR, c3LOC, l3LOC, &l3LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLGetData(stmt, 3, SQL_C_TEXT_LOCATOR, c4LOC, l4LOC, &l4LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLFreeStmt(stmt, SQL_UNBIND);
	sr = SQLFreeStmt(stmt, SQL_RESET_PARAMS);
	sr = SQLFreeStmt(stmt, SQL_CLOSE);
	//Char length
	//Char length TEXT
	int textCharLength = 0;
	SQLLEN TCLLength = sizeof(int);
	sr = SQLBindParameter(stmt, 1, SQL_PARAM_INPUT, SQL_C_TEXT_LOCATOR, SQL_TEXT_LOCATOR, l2LOC, 0, c2LOC, l2LOC, &l2LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLBindParameter(stmt, 2, SQL_PARAM_OUTPUT, SQL_C_LONG, SQL_INTEGER, TCLLength, 0, &textCharLength, TCLLength, &TCLLength);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLExecDirect(stmt, charLEN_TEXT_SQL, SQL_NTS);
	printError(sr, SQL_HANDLE_STMT, stmt);
	//Char length TEXT Cleanup
	sr = SQLFreeStmt(stmt, SQL_UNBIND);
	sr = SQLFreeStmt(stmt, SQL_RESET_PARAMS);
	sr = SQLFreeStmt(stmt, SQL_CLOSE);
	//Char length UNITEXT
	int unitextCharLength = 0;
	SQLLEN UCLLength = sizeof(int);
	sr = SQLBindParameter(stmt, 1, SQL_PARAM_INPUT, SQL_C_UNITEXT_LOCATOR, SQL_UNITEXT_LOCATOR, l3LOC, 0, c3LOC, l3LOC, &l3LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLBindParameter(stmt, 2, SQL_PARAM_OUTPUT, SQL_C_LONG, SQL_INTEGER, UCLLength, 0, &unitextCharLength, UCLLength, &UCLLength);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLExecDirect(stmt, charLEN_UNITEXT_SQL, SQL_NTS);
	printError(sr, SQL_HANDLE_STMT, stmt);
	//Char length UNITEXT Cleanup
	sr = SQLFreeStmt(stmt, SQL_UNBIND);
	sr = SQLFreeStmt(stmt, SQL_RESET_PARAMS);
	sr = SQLFreeStmt(stmt, SQL_CLOSE);
	//Char length IMAGE
	//Char length is not valid for IMAGE locators
	sr = SQLEndTran(SQL_HANDLE_DBC, dbc, SQL_COMMIT);
	sr = SQLSetConnectAttr(dbc, SQL_ATTR_AUTOCOMMIT, (SQLPOINTER)SQL_AUTOCOMMIT_ON, 0);
}

void ByteLength(SQLHDBC dbc, SQLHSTMT stmt)
{
	SQLRETURN sr;
	sr = SQLSetConnectAttr(dbc, SQL_ATTR_AUTOCOMMIT, (SQLPOINTER)SQL_AUTOCOMMIT_OFF, 0);
	//Get a locator from the server
	unsigned char c2LOC[SQL_LOCATOR_SIZE];
	SQLLEN l2LOC = sizeof(c2LOC);
	unsigned char c3LOC[SQL_LOCATOR_SIZE];
	SQLLEN l3LOC = sizeof(c3LOC);
	unsigned char c4LOC[SQL_LOCATOR_SIZE];
	SQLLEN l4LOC = sizeof(c4LOC);
	int id = 3;
	int c1 = 4;
	SQLLEN l1 = sizeof(int);
	SQLLEN idLen = sizeof(int);
	sr = SQLBindParameter(stmt, 1, SQL_PARAM_INPUT, SQL_C_LONG, SQL_INTEGER, idLen, 0, &id, idLen, &idLen);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLExecDirect(stmt, selectCOL_SQL, SQL_NTS);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLFetch(stmt);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLGetData(stmt, 1, SQL_C_TEXT_LOCATOR, c2LOC, l2LOC, &l2LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLGetData(stmt, 2, SQL_C_TEXT_LOCATOR, c3LOC, l3LOC, &l3LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLGetData(stmt, 3, SQL_C_TEXT_LOCATOR, c4LOC, l4LOC, &l4LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLFreeStmt(stmt, SQL_UNBIND);
	sr = SQLFreeStmt(stmt, SQL_RESET_PARAMS);
	sr = SQLFreeStmt(stmt, SQL_CLOSE);
	//Byte length
	//Byte length TEXT
	int textByteLength = 0;
	SQLLEN TBLLength = sizeof(int);
	sr = SQLBindParameter(stmt, 1, SQL_PARAM_INPUT, SQL_C_TEXT_LOCATOR, SQL_TEXT_LOCATOR, l2LOC, 0, c2LOC, l2LOC, &l2LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLBindParameter(stmt, 2, SQL_PARAM_OUTPUT, SQL_C_LONG, SQL_INTEGER, TBLLength, 0, &textByteLength, TBLLength, &TBLLength);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLExecDirect(stmt, byteLEN_TEXT_SQL, SQL_NTS);
	printError(sr, SQL_HANDLE_STMT, stmt);
	//Byte length TEXT Cleanup
	sr = SQLFreeStmt(stmt, SQL_UNBIND);
	sr = SQLFreeStmt(stmt, SQL_RESET_PARAMS);
	sr = SQLFreeStmt(stmt, SQL_CLOSE);
	//Byte length UNITEXT
	int unitextByteLength = 0;
	SQLLEN UBLLength = sizeof(int);
	sr = SQLBindParameter(stmt, 1, SQL_PARAM_INPUT, SQL_C_UNITEXT_LOCATOR, SQL_UNITEXT_LOCATOR, l3LOC, 0, c3LOC, l3LOC, &l3LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLBindParameter(stmt, 2, SQL_PARAM_OUTPUT, SQL_C_LONG, SQL_INTEGER, UBLLength, 0, &unitextByteLength, UBLLength, &UBLLength);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLExecDirect(stmt, byteLEN_UNITEXT_SQL, SQL_NTS);
	printError(sr, SQL_HANDLE_STMT, stmt);
	//Byte length UNITEXT Cleanup
	sr = SQLFreeStmt(stmt, SQL_UNBIND);
	sr = SQLFreeStmt(stmt, SQL_RESET_PARAMS);
	sr = SQLFreeStmt(stmt, SQL_CLOSE);
	//Byte length IMAGE
	int imageByteLength = 0;
	SQLLEN IBLLength = sizeof(int);
	sr = SQLBindParameter(stmt, 1, SQL_PARAM_INPUT, SQL_C_IMAGE_LOCATOR, SQL_IMAGE_LOCATOR, l4LOC, 0, c4LOC, l4LOC, &l4LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLBindParameter(stmt, 2, SQL_PARAM_OUTPUT, SQL_C_LONG, SQL_INTEGER, IBLLength, 0, &imageByteLength, IBLLength, &IBLLength);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLExecDirect(stmt, byteLEN_IMAGE_SQL, SQL_NTS);
	printError(sr, SQL_HANDLE_STMT, stmt);
	//Byte length IMAGE Cleanup
	sr = SQLFreeStmt(stmt, SQL_UNBIND);
	sr = SQLFreeStmt(stmt, SQL_RESET_PARAMS);
	sr = SQLFreeStmt(stmt, SQL_CLOSE);
	sr = SQLEndTran(SQL_HANDLE_DBC, dbc, SQL_COMMIT);
	sr = SQLSetConnectAttr(dbc, SQL_ATTR_AUTOCOMMIT, (SQLPOINTER)SQL_AUTOCOMMIT_ON, 0);
}

void IndexofLocator(SQLHDBC dbc, SQLHSTMT stmt)
{
	SQLRETURN sr;
	sr = SQLSetConnectAttr(dbc, SQL_ATTR_AUTOCOMMIT, (SQLPOINTER)SQL_AUTOCOMMIT_OFF, 0);
	//Get a locator from the server
	unsigned char c2LOC[SQL_LOCATOR_SIZE];
	SQLLEN l2LOC = sizeof(c2LOC);
	unsigned char c3LOC[SQL_LOCATOR_SIZE];
	SQLLEN l3LOC = sizeof(c3LOC);
	unsigned char c4LOC[SQL_LOCATOR_SIZE];
	SQLLEN l4LOC = sizeof(c4LOC);
	int id = 3;
	int c1 = 4;
	SQLLEN l1 = sizeof(int);
	SQLLEN idLen = sizeof(int);
	sr = SQLBindParameter(stmt, 1, SQL_PARAM_INPUT, SQL_C_LONG, SQL_INTEGER, idLen, 0, &id, idLen, &idLen);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLExecDirect(stmt, selectCOL_SQL, SQL_NTS);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLFetch(stmt);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLGetData(stmt, 1, SQL_C_TEXT_LOCATOR, c2LOC, l2LOC, &l2LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLGetData(stmt, 2, SQL_C_TEXT_LOCATOR, c3LOC, l3LOC, &l3LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLGetData(stmt, 3, SQL_C_TEXT_LOCATOR, c4LOC, l4LOC, &l4LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLFreeStmt(stmt, SQL_UNBIND);
	sr = SQLFreeStmt(stmt, SQL_RESET_PARAMS);
	sr = SQLFreeStmt(stmt, SQL_CLOSE);
	//Indexof locator
	//Indexof locator TEXT
	int textIndex = 20;
	SQLLEN TILength = sizeof(int);
	int startLocation = 1;
	SQLLEN SLLength = sizeof(int);
	sr = SQLBindParameter(stmt, 1, SQL_PARAM_INPUT, SQL_C_TEXT_LOCATOR, SQL_TEXT_LOCATOR, l2LOC, 0, c2LOC, l2LOC, &l2LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLBindParameter(stmt, 2, SQL_PARAM_INPUT, SQL_C_TEXT_LOCATOR, SQL_TEXT_LOCATOR, l2LOC, 0, c2LOC, l2LOC, &l2LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLBindParameter(stmt, 3, SQL_PARAM_INPUT, SQL_C_LONG, SQL_INTEGER, SLLength, 0, &startLocation, SLLength, &SLLength);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLBindParameter(stmt, 4, SQL_PARAM_OUTPUT, SQL_C_LONG, SQL_INTEGER, TILength, 0, &textIndex, TILength, &TILength);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLExecDirect(stmt, charINDEX_TEXT_SQL, SQL_NTS);
	printError(sr, SQL_HANDLE_STMT, stmt);
	//Indexof locator TEXT Cleanup
	sr = SQLFreeStmt(stmt, SQL_UNBIND);
	sr = SQLFreeStmt(stmt, SQL_RESET_PARAMS);
	sr = SQLFreeStmt(stmt, SQL_CLOSE);

	if (textIndex != 1)
	{
		cout << "Error Indexof locator TEXT is wrong" << endl;
	}

	//Indexof UNITEXT
	//Indexof is not supported for unitext locators
	//Indexof locator IMAGE
	int imageIndex = 20;
	SQLLEN IILength = sizeof(int);
	sr = SQLBindParameter(stmt, 1, SQL_PARAM_INPUT, SQL_C_IMAGE_LOCATOR, SQL_IMAGE_LOCATOR, l4LOC, 0, c4LOC, l4LOC, &l4LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLBindParameter(stmt, 2, SQL_PARAM_INPUT, SQL_C_IMAGE_LOCATOR, SQL_IMAGE_LOCATOR, l4LOC, 0, c4LOC, l4LOC, &l4LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLBindParameter(stmt, 3, SQL_PARAM_INPUT, SQL_C_LONG, SQL_INTEGER, SLLength, 0, &startLocation, SLLength, &SLLength);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLBindParameter(stmt, 4, SQL_PARAM_OUTPUT, SQL_C_LONG, SQL_INTEGER, IILength, 0, &imageIndex, IILength, &IILength);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLExecDirect(stmt, charINDEX_UNITEXT_SQL, SQL_NTS);
	printError(sr, SQL_HANDLE_STMT, stmt);
	//Indexof locator IMAGE Cleanup
	sr = SQLFreeStmt(stmt, SQL_UNBIND);
	sr = SQLFreeStmt(stmt, SQL_RESET_PARAMS);
	sr = SQLFreeStmt(stmt, SQL_CLOSE);

	if (imageIndex != 1)
	{
		cout << "Error Indexof locator IMAGE is wrong" << endl;
	}

	sr = SQLEndTran(SQL_HANDLE_DBC, dbc, SQL_COMMIT);
	sr = SQLSetConnectAttr(dbc, SQL_ATTR_AUTOCOMMIT, (SQLPOINTER)SQL_AUTOCOMMIT_ON, 0);
}

void Indexof(SQLHDBC dbc, SQLHSTMT stmt)
{
	SQLRETURN sr;
	sr = SQLSetConnectAttr(dbc, SQL_ATTR_AUTOCOMMIT, (SQLPOINTER)SQL_AUTOCOMMIT_OFF, 0);
	//Get a locator from the server
	unsigned char c2LOC[SQL_LOCATOR_SIZE];
	SQLLEN l2LOC = sizeof(c2LOC);
	unsigned char c3LOC[SQL_LOCATOR_SIZE];
	SQLLEN l3LOC = sizeof(c3LOC);
	unsigned char c4LOC[SQL_LOCATOR_SIZE];
	SQLLEN l4LOC = sizeof(c4LOC);
	int id = 3;
	int c1 = 4;
	SQLLEN l1 = sizeof(int);
	SQLLEN idLen = sizeof(int);
	unsigned char iSubstr[5] = {0x05, 0x04, 0x03, 0x02, 0x01};
	SQLCHAR cSubstr[10] = "Alpha";
	SQLLEN lSubstr = 5;
	sr = SQLBindParameter(stmt, 1, SQL_PARAM_INPUT, SQL_C_LONG, SQL_INTEGER, idLen, 0, &id, idLen, &idLen);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLExecDirect(stmt, selectCOL_SQL, SQL_NTS);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLFetch(stmt);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLGetData(stmt, 1, SQL_C_TEXT_LOCATOR, c2LOC, l2LOC, &l2LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLGetData(stmt, 2, SQL_C_TEXT_LOCATOR, c3LOC, l3LOC, &l3LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLGetData(stmt, 3, SQL_C_TEXT_LOCATOR, c4LOC, l4LOC, &l4LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLFreeStmt(stmt, SQL_UNBIND);
	sr = SQLFreeStmt(stmt, SQL_RESET_PARAMS);
	sr = SQLFreeStmt(stmt, SQL_CLOSE);
	//Indexof
	//Indexof TEXT
	int textIndex = 0;
	SQLLEN TILength = sizeof(int);
	int startLocation = 1;
	SQLLEN SLLength = sizeof(int);
	sr = SQLBindParameter(stmt, 1, SQL_PARAM_INPUT, SQL_C_CHAR, SQL_CHAR, lSubstr, 0, &cSubstr, lSubstr, &lSubstr);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLBindParameter(stmt, 2, SQL_PARAM_INPUT, SQL_C_TEXT_LOCATOR, SQL_TEXT_LOCATOR, l2LOC, 0, c2LOC, l2LOC, &l2LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLBindParameter(stmt, 3, SQL_PARAM_INPUT, SQL_C_LONG, SQL_INTEGER, SLLength, 0, &startLocation, SLLength, &SLLength);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLBindParameter(stmt, 4, SQL_PARAM_OUTPUT, SQL_C_LONG, SQL_INTEGER, TILength, 0, &textIndex, TILength, &TILength);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLExecDirect(stmt, varcharINDEX_SQL, SQL_NTS);
	printError(sr, SQL_HANDLE_STMT, stmt);
	//Indexof TEXT Cleanup
	sr = SQLFreeStmt(stmt, SQL_UNBIND);
	sr = SQLFreeStmt(stmt, SQL_RESET_PARAMS);
	sr = SQLFreeStmt(stmt, SQL_CLOSE);
	//Indexof UNITEXT
	//Indexof is not supported for unitext locators
	//Indexof IMAGE
	int imageIndex = 0;
	SQLLEN IILength = sizeof(int);
	sr = SQLBindParameter(stmt, 1, SQL_PARAM_INPUT, SQL_C_BINARY, SQL_BINARY, lSubstr, 0, &iSubstr, lSubstr, &lSubstr);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLBindParameter(stmt, 2, SQL_PARAM_INPUT, SQL_C_IMAGE_LOCATOR, SQL_IMAGE_LOCATOR, l4LOC, 0, c4LOC, l4LOC, &l4LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLBindParameter(stmt, 3, SQL_PARAM_INPUT, SQL_C_LONG, SQL_INTEGER, SLLength, 0, &startLocation, SLLength, &SLLength);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLBindParameter(stmt, 4, SQL_PARAM_OUTPUT, SQL_C_LONG, SQL_INTEGER, IILength, 0, &imageIndex, IILength, &IILength);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLExecDirect(stmt, varbinINDEX_SQL, SQL_NTS);
	printError(sr, SQL_HANDLE_STMT, stmt);
	//Indexof IMAGE Cleanup
	sr = SQLFreeStmt(stmt, SQL_UNBIND);
	sr = SQLFreeStmt(stmt, SQL_RESET_PARAMS);
	sr = SQLFreeStmt(stmt, SQL_CLOSE);
	sr = SQLEndTran(SQL_HANDLE_DBC, dbc, SQL_COMMIT);
	sr = SQLSetConnectAttr(dbc, SQL_ATTR_AUTOCOMMIT, (SQLPOINTER)SQL_AUTOCOMMIT_ON, 0);
}

void PatternIndexof(SQLHDBC dbc, SQLHSTMT stmt)
{
	SQLRETURN sr;
	sr = SQLSetConnectAttr(dbc, SQL_ATTR_AUTOCOMMIT, (SQLPOINTER)SQL_AUTOCOMMIT_OFF, 0);
	//Get a locator from the server
	unsigned char c2LOC[SQL_LOCATOR_SIZE];
	SQLLEN l2LOC = sizeof(c2LOC);
	unsigned char c3LOC[SQL_LOCATOR_SIZE];
	SQLLEN l3LOC = sizeof(c3LOC);
	unsigned char c4LOC[SQL_LOCATOR_SIZE];
	SQLLEN l4LOC = sizeof(c4LOC);
	int id = 3;
	int c1 = 4;
	SQLLEN l1 = sizeof(int);
	SQLLEN idLen = sizeof(int);
	sr = SQLBindParameter(stmt, 1, SQL_PARAM_INPUT, SQL_C_LONG, SQL_INTEGER, idLen, 0, &id, idLen, &idLen);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLExecDirect(stmt, selectCOL_SQL, SQL_NTS);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLFetch(stmt);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLGetData(stmt, 1, SQL_C_TEXT_LOCATOR, c2LOC, l2LOC, &l2LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLGetData(stmt, 2, SQL_C_TEXT_LOCATOR, c3LOC, l3LOC, &l3LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLGetData(stmt, 3, SQL_C_TEXT_LOCATOR, c4LOC, l4LOC, &l4LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLFreeStmt(stmt, SQL_UNBIND);
	sr = SQLFreeStmt(stmt, SQL_RESET_PARAMS);
	sr = SQLFreeStmt(stmt, SQL_CLOSE);
	//Pattern index
	//Pattern index TEXT
	int textPatIndex = 0;
	SQLCHAR pattern[8] = "%Alpha%";
	SQLLEN lPattern = 7;
	SQLLEN TILength = sizeof(int);
	sr = SQLBindParameter(stmt, 1, SQL_PARAM_INPUT, SQL_C_CHAR, SQL_CHAR, lPattern, 0, pattern, lPattern, &lPattern);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLBindParameter(stmt, 2, SQL_PARAM_INPUT, SQL_C_TEXT_LOCATOR, SQL_TEXT_LOCATOR, l2LOC, 0, c2LOC, l2LOC, &l2LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLBindParameter(stmt, 3, SQL_PARAM_OUTPUT, SQL_C_LONG, SQL_INTEGER, TILength, 0, &textPatIndex, TILength, &TILength);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLExecDirect(stmt, patINDEX_SQL, SQL_NTS);
	printError(sr, SQL_HANDLE_STMT, stmt);
	//Pattern index TEXT Cleanup
	sr = SQLFreeStmt(stmt, SQL_UNBIND);
	sr = SQLFreeStmt(stmt, SQL_RESET_PARAMS);
	sr = SQLFreeStmt(stmt, SQL_CLOSE);
	//Pattern index UNITEXT
	//Pattern index is not supported for unitext locators
	//Pattern index IMAGE
	//Pattern index is not supported for images locators
	sr = SQLEndTran(SQL_HANDLE_DBC, dbc, SQL_COMMIT);
	sr = SQLSetConnectAttr(dbc, SQL_ATTR_AUTOCOMMIT, (SQLPOINTER)SQL_AUTOCOMMIT_ON, 0);
}

void LocatorValid(SQLHDBC dbc, SQLHSTMT stmt)
{
	SQLRETURN sr;
	sr = SQLSetConnectAttr(dbc, SQL_ATTR_AUTOCOMMIT, (SQLPOINTER)SQL_AUTOCOMMIT_OFF, 0);
	//Get a locator from the server
	unsigned char c2LOC[SQL_LOCATOR_SIZE];
	SQLLEN l2LOC = sizeof(c2LOC);
	unsigned char c3LOC[SQL_LOCATOR_SIZE];
	SQLLEN l3LOC = sizeof(c3LOC);
	unsigned char c4LOC[SQL_LOCATOR_SIZE];
	SQLLEN l4LOC = sizeof(c4LOC);
	int id = 3;
	int c1 = 4;
	SQLLEN l1 = sizeof(int);
	SQLLEN idLen = sizeof(int);
	sr = SQLBindParameter(stmt, 1, SQL_PARAM_INPUT, SQL_C_LONG, SQL_INTEGER, idLen, 0, &id, idLen, &idLen);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLExecDirect(stmt, selectCOL_SQL, SQL_NTS);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLFetch(stmt);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLGetData(stmt, 1, SQL_C_TEXT_LOCATOR, c2LOC, l2LOC, &l2LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLGetData(stmt, 2, SQL_C_TEXT_LOCATOR, c3LOC, l3LOC, &l3LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLGetData(stmt, 3, SQL_C_TEXT_LOCATOR, c4LOC, l4LOC, &l4LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLFreeStmt(stmt, SQL_UNBIND);
	sr = SQLFreeStmt(stmt, SQL_RESET_PARAMS);
	sr = SQLFreeStmt(stmt, SQL_CLOSE);
	//Locator valid
	//Locator valid TEXT
	sr = SQLBindParameter(stmt, 1, SQL_PARAM_INPUT, SQL_C_TEXT_LOCATOR, SQL_TEXT_LOCATOR, l2LOC, 0, c2LOC, l2LOC, &l2LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	bool valid = false;
	SQLLEN validLength = sizeof(bool);
	sr = SQLBindParameter(stmt, 2, SQL_PARAM_OUTPUT, SQL_C_BIT, SQL_BIT, validLength, 0, &valid, validLength, &validLength);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLExecDirect(stmt, validTEXT_LOC_SQL, SQL_NTS);
	printError(sr, SQL_HANDLE_STMT, stmt);

	if (!valid)
	{
		cout << "Valid TEXT locator marked as invalid" << endl;
	}

	//Locator valid TEXT Cleanup
	sr = SQLFreeStmt(stmt, SQL_UNBIND);
	sr = SQLFreeStmt(stmt, SQL_RESET_PARAMS);
	sr = SQLFreeStmt(stmt, SQL_CLOSE);
	//Locator valid UNITEXT
	sr = SQLBindParameter(stmt, 1, SQL_PARAM_INPUT, SQL_C_UNITEXT_LOCATOR, SQL_UNITEXT_LOCATOR, l3LOC, 0, c3LOC, l3LOC, &l3LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	valid = false;
	validLength = sizeof(bool);
	sr = SQLBindParameter(stmt, 2, SQL_PARAM_OUTPUT, SQL_C_BIT, SQL_BIT, validLength, 0, &valid, validLength, &validLength);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLExecDirect(stmt, validUNITEXT_LOC_SQL, SQL_NTS);
	printError(sr, SQL_HANDLE_STMT, stmt);

	if (!valid)
	{
		cout << "Valid UNITEXT locator marked as invalid" << endl;
	}

	//Locator valid UNITEXT Cleanup
	sr = SQLFreeStmt(stmt, SQL_UNBIND);
	sr = SQLFreeStmt(stmt, SQL_RESET_PARAMS);
	sr = SQLFreeStmt(stmt, SQL_CLOSE);
	//Locator valid IMAGE
	sr = SQLBindParameter(stmt, 1, SQL_PARAM_INPUT, SQL_C_IMAGE_LOCATOR, SQL_IMAGE_LOCATOR, l4LOC, 0, c4LOC, l4LOC, &l4LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	valid = false;
	validLength = sizeof(bool);
	sr = SQLBindParameter(stmt, 2, SQL_PARAM_OUTPUT, SQL_C_BIT, SQL_BIT, validLength, 0, &valid, validLength, &validLength);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLExecDirect(stmt, validIMAGE_LOC_SQL, SQL_NTS);
	printError(sr, SQL_HANDLE_STMT, stmt);

	if (!valid)
	{
		cout << "Valid IMAGE locator marked as invalid" << endl;
	}

	//Locator valid IMAGE Cleanup
	sr = SQLFreeStmt(stmt, SQL_UNBIND);
	sr = SQLFreeStmt(stmt, SQL_RESET_PARAMS);
	sr = SQLFreeStmt(stmt, SQL_CLOSE);
	sr = SQLEndTran(SQL_HANDLE_DBC, dbc, SQL_COMMIT);
	sr = SQLSetConnectAttr(dbc, SQL_ATTR_AUTOCOMMIT, (SQLPOINTER)SQL_AUTOCOMMIT_ON, 0);
}

void Deallocate(SQLHDBC dbc, SQLHSTMT stmt)
{
	SQLRETURN sr;
	sr = SQLSetConnectAttr(dbc, SQL_ATTR_AUTOCOMMIT, (SQLPOINTER)SQL_AUTOCOMMIT_OFF, 0);
	//Get a locator from the server
	unsigned char c2LOC[SQL_LOCATOR_SIZE];
	SQLLEN l2LOC = sizeof(c2LOC);
	unsigned char c3LOC[SQL_LOCATOR_SIZE];
	SQLLEN l3LOC = sizeof(c3LOC);
	unsigned char c4LOC[SQL_LOCATOR_SIZE];
	SQLLEN l4LOC = sizeof(c4LOC);
	int id = 3;
	int c1 = 4;
	SQLLEN l1 = sizeof(int);
	SQLLEN idLen = sizeof(int);
	sr = SQLBindParameter(stmt, 1, SQL_PARAM_INPUT, SQL_C_LONG, SQL_INTEGER, idLen, 0, &id, idLen, &idLen);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLExecDirect(stmt, selectCOL_SQL, SQL_NTS);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLFetch(stmt);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLGetData(stmt, 1, SQL_C_TEXT_LOCATOR, c2LOC, l2LOC, &l2LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLGetData(stmt, 2, SQL_C_TEXT_LOCATOR, c3LOC, l3LOC, &l3LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLGetData(stmt, 3, SQL_C_TEXT_LOCATOR, c4LOC, l4LOC, &l4LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLFreeStmt(stmt, SQL_UNBIND);
	sr = SQLFreeStmt(stmt, SQL_RESET_PARAMS);
	sr = SQLFreeStmt(stmt, SQL_CLOSE);
	//Deallocate
	//Deallocate TEXT
	sr = SQLBindParameter(stmt, 1, SQL_PARAM_INPUT, SQL_C_TEXT_LOCATOR, SQL_TEXT_LOCATOR, l2LOC, 0, c2LOC, l2LOC, &l2LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLExecDirect(stmt, deallocateLOC_SQL, SQL_NTS);
	printError(sr, SQL_HANDLE_STMT, stmt);
	//Deallocate TEXT Cleanup
	sr = SQLFreeStmt(stmt, SQL_UNBIND);
	sr = SQLFreeStmt(stmt, SQL_RESET_PARAMS);
	sr = SQLFreeStmt(stmt, SQL_CLOSE);
	//Deallocate UNITEXT
	sr = SQLBindParameter(stmt, 1, SQL_PARAM_INPUT, SQL_C_UNITEXT_LOCATOR, SQL_UNITEXT_LOCATOR, l3LOC, 0, c3LOC, l3LOC, &l3LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLExecDirect(stmt, deallocateLOC_SQL, SQL_NTS);
	printError(sr, SQL_HANDLE_STMT, stmt);
	//Deallocate UNITEXT Cleanup
	sr = SQLFreeStmt(stmt, SQL_UNBIND);
	sr = SQLFreeStmt(stmt, SQL_RESET_PARAMS);
	sr = SQLFreeStmt(stmt, SQL_CLOSE);
	//Deallocate IMAGE
	sr = SQLBindParameter(stmt, 1, SQL_PARAM_INPUT, SQL_C_IMAGE_LOCATOR, SQL_IMAGE_LOCATOR, l4LOC, 0, c4LOC, l4LOC, &l4LOC);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLExecDirect(stmt, deallocateLOC_SQL, SQL_NTS);
	printError(sr, SQL_HANDLE_STMT, stmt);
	//Deallocate IMAGE Cleanup
	sr = SQLFreeStmt(stmt, SQL_UNBIND);
	sr = SQLFreeStmt(stmt, SQL_RESET_PARAMS);
	sr = SQLFreeStmt(stmt, SQL_CLOSE);
	sr = SQLEndTran(SQL_HANDLE_DBC, dbc, SQL_COMMIT);
	sr = SQLSetConnectAttr(dbc, SQL_ATTR_AUTOCOMMIT, (SQLPOINTER)SQL_AUTOCOMMIT_ON, 0);
}

void printTable(SQLHSTMT stmt)
{
	//If enableloblocator=0 then to retrieve a lob nothing changes: select bk_desc from books
	//To retrieve a LOB locator you would use select create_locator(text_locator, bk_desc) from books
	//If enableloblocator=1 then to retrieve a lob : select return_lob(text, create_locator(text_locator, bk_desc)) from books
	//To retrieve a LOB locator you would use select bk_desc from books
	int c1;
	SQLLEN c1Len = sizeof(int);
	SQLCHAR c2[5000];
	SQLLEN c2Len = 5000;
	SQLWCHAR c3[5000];
	SQLLEN c3Len = 5000;
	unsigned char c4[5000];
	SQLLEN c4Len = 5000;
	SQLRETURN sr = SQL_ERROR;
	sr = SQLExecDirect(stmt, selectStmt, SQL_NTS);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLBindCol(stmt, 1, SQL_C_LONG, &c1, c1Len, &c1Len);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLFetch(stmt);
	printError(sr, SQL_HANDLE_STMT, stmt);

	while (sr == SQL_SUCCESS || sr == SQL_SUCCESS_WITH_INFO)
	{
		SQLLEN c4Len = 5000;
		SQLLEN c3Len = 5000;
		SQLLEN c2Len = 5000;
		sr = SQLGetData(stmt, 2, SQL_C_CHAR, c2, c2Len, &c2Len);
		printError(sr, SQL_HANDLE_STMT, stmt);
		sr = SQLGetData(stmt, 3, SQL_C_WCHAR, c3, c3Len, &c3Len);
		printError(sr, SQL_HANDLE_STMT, stmt);
		sr = SQLGetData(stmt, 4, SQL_C_BINARY, c4, c4Len, &c4Len);
		printError(sr, SQL_HANDLE_STMT, stmt);
		cout << c1 << endl << endl;
		cout << c2;
		cout << endl << endl;
		printBinary((unsigned char*)c3, (int)c3Len);
		cout << endl << endl;
		printBinary(c4, (int)c4Len);
		cout << endl << endl;

		for (int i = 0; i < 80; i++)
		{
			cout << "-";
		}

		cout << endl;
		sr = SQLFetch(stmt);
	}

	sr = SQLFreeStmt(stmt, SQL_UNBIND);
	sr = SQLFreeStmt(stmt, SQL_RESET_PARAMS);
	sr = SQLFreeStmt(stmt, SQL_CLOSE);
}

void createTable(SQLHSTMT stmt)
{
	dropTable(stmt);
	SQLRETURN sr = SQLExecDirect(stmt, createTableStmt, SQL_NTS);
	printError(sr, SQL_HANDLE_STMT, stmt);
}

void dropTable(SQLHSTMT stmt)
{
	SQLRETURN sr = SQLExecDirect(stmt, dropTableStmt, SQL_NTS);
}

#if defined(WIN32) && defined(UNICODE)
void connect(SQLHENV* env, SQLHDBC* dbc, SQLHSTMT* stmt, int argc, wchar_t* argv[])
#else
void connect(SQLHENV* env, SQLHDBC* dbc, SQLHSTMT* stmt, int argc, char* argv[])
#endif
{
	SQLRETURN sr;
	SQLTCHAR connString[512];
	int lengthOfDefault = strlen("DSN=sampledsn");
	SQLTCHAR* extraProps = _ODBCSTRTYPE("enableloblocator=1;dynamicprepare=1;usecursor=1;");
	int extraPropsLen = (int)strlen("enableloblocator=1;dynamicprepare=1;usecursor=1;");
	memcpy(connString, extraProps, extraPropsLen*sizeof(SQLTCHAR));
	sr = SQLAllocHandle(SQL_HANDLE_ENV, SQL_NULL_HANDLE, env);

	if (sr != SQL_SUCCESS && sr != SQL_SUCCESS_WITH_INFO)
	{
		printf("Allocating Environment Handle failed; SQLRETURN code is :%i", sr);
		exit(1);
	}

	sr = SQLSetEnvAttr(*env, SQL_ATTR_ODBC_VERSION, (void*)SQL_OV_ODBC3, 0);
	sr = SQLAllocHandle(SQL_HANDLE_DBC, *env, dbc);

	if (sr != SQL_SUCCESS && sr != SQL_SUCCESS_WITH_INFO)
	{
		printError(sr, SQL_HANDLE_ENV, *env);
		finish(*env, *dbc, SQL_NULL_HANDLE, true);
	}

	if(argc == 4)
	{
#if defined(UNICODE)
#if defined(WIN32)
		wstring tmpConnString = wstring(L"DSN=");
		tmpConnString += wstring(argv[1]);
		tmpConnString += wstring(L";UID=");
		tmpConnString += wstring(argv[2]);
		tmpConnString += wstring(L";PWD=");
		tmpConnString += wstring(argv[3]);
		wcout << L"Using connection string \"" << tmpConnString.c_str() << L"\"" << endl;
		memcpy(connString + extraPropsLen, tmpConnString.c_str(), tmpConnString.length()*sizeof(SQLTCHAR));
		connString[tmpConnString.length() + extraPropsLen] = 0;
#else
		//The connection string is hard coded because wmain is non-standared c++
		//A complete string converter, which is not in the scope of this sample, would be required for command line input
		//NOTE we are only able to build with UNICODE defined on platforms that allow the
		//redefinition of wchar_t from 32bit to 16bit to match SQLWCHAR
		cout << "Using connection string \"DSN=sampledsn\"" << endl;
		memcpy(connString + extraPropsLen, _ODBCSTRTYPE("DSN=sampledsn"), lengthOfDefault*sizeof(SQLTCHAR));
		connString[lengthOfDefault + extraPropsLen] = 0;
#endif
#else
		string tmpConnString = string("DSN=");
		tmpConnString += string(argv[1]);
		tmpConnString += string(";UID=");
		tmpConnString += string(argv[2]);
		tmpConnString += string(";PWD=");
		tmpConnString += string(argv[3]);
		cout << "Using connection string \"" << tmpConnString.c_str() << "\"" << endl;
		memcpy(connString + extraPropsLen, tmpConnString.c_str(), tmpConnString.length()*sizeof(SQLTCHAR));
		connString[tmpConnString.length() + extraPropsLen] = 0;
#endif
	}
	else
	{
		cout << "Using connection string \"DSN=sampledsn\"" << endl;
		memcpy(connString + extraPropsLen, _ODBCSTRTYPE("DSN=sampledsn"), lengthOfDefault*sizeof(SQLTCHAR));
		connString[lengthOfDefault + extraPropsLen] = 0;
	}

	sr = SQLDriverConnect(*dbc, SQL_NULL_HANDLE, connString, SQL_NTS, SQL_NULL_HANDLE, 0, SQL_NULL_HANDLE, SQL_DRIVER_NOPROMPT);

	if (sr != SQL_SUCCESS && sr != SQL_SUCCESS_WITH_INFO)
	{
		printError(sr, SQL_HANDLE_DBC, *dbc);
		finish(*env, *dbc, SQL_NULL_HANDLE, true);
	}

	sr = SQLAllocHandle(SQL_HANDLE_STMT, *dbc, stmt);
}

void finish(SQLHENV env, SQLHDBC dbc, SQLHSTMT stmt, bool doExit)
{
	if (stmt != SQL_NULL_HANDLE)
	{
		dropTable(stmt);
		SQLFreeStmt(stmt, SQL_CLOSE);
		SQLFreeHandle(SQL_HANDLE_STMT, stmt);
	}

	if (dbc != SQL_NULL_HANDLE)
	{
		SQLDisconnect(dbc);
		SQLFreeHandle(SQL_HANDLE_DBC, dbc);
	}

	if (env != SQL_NULL_HANDLE)
	{
		SQLFreeHandle(SQL_HANDLE_ENV, env);
	}

	if (doExit)
	{
		exit(1);
	}
}

void printError(SQLRETURN retcode, SQLSMALLINT handleType, SQLHANDLE handle)
{
	SQLTCHAR errormsg[ERR_MSG_LEN];
	SQLTCHAR sqlstate[SQL_SQLSTATE_SIZE+1];
	SQLINTEGER nativeerror = 0;
	SQLSMALLINT errormsglen = 0;

	if (retcode == SQL_ERROR)
	{
		retcode = SQLGetDiagRec(handleType, handle, 1, sqlstate, &nativeerror, errormsg, ERR_MSG_LEN, &errormsglen);

		if (retcode == SQL_SUCCESS || retcode == SQL_SUCCESS_WITH_INFO)
		{
			printf("SqlState: %s Error Message: %s\n", sqlstate, errormsg);
		}

		exit(1);
	}
}
