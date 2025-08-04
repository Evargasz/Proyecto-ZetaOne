/*
Copyright (c) 2010  Sybase, Inc.

Module Name:
	odbcbatch.cpp

Abstract:
 	Sample ODBC console application.
 	Demonstrates the use of the ODBC batching feature.

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

#define ARRAY_SIZE(a) (sizeof(a)/sizeof(a[0]))
#define ERR_MSG_LEN	255
#define BATCH_SIZE 10

SQLTCHAR* createTableStmt = _ODBCSTRTYPE("create table odbcbatch (c1 int, c2 text)");
SQLTCHAR* dropTableStmt = _ODBCSTRTYPE("drop table odbcbatch");
SQLTCHAR* insertStmt = _ODBCSTRTYPE("insert into odbcbatch values (?, ?)");
SQLTCHAR* selectStmt = _ODBCSTRTYPE("select c1, c2 from odbcbatch");

#if defined(WIN32) && defined(UNICODE)
void connect(SQLHENV* env, SQLHDBC* dbc, SQLHSTMT* stmt, int argc, wchar_t* argv[]);
#else
void connect(SQLHENV* env, SQLHDBC* dbc, SQLHSTMT* stmt, int argc, char* argv[]);
#endif
void finish(SQLHENV env, SQLHDBC dbc, SQLHSTMT stmt, bool doExit);
void createTable(SQLHSTMT stmt);
void dropTable(SQLHSTMT stmt);
void dumpResults(char* title, SQLHSTMT stmt);
void printError(SQLRETURN retcode, SQLSMALLINT handleType, SQLHANDLE handle);

void runBatch(SQLHDBC dbc, SQLHSTMT stmt);
void runArray(SQLHDBC dbc, SQLHSTMT stmt);


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
	runBatch(dbc, stmt);
	dumpResults("runBatch", stmt);
	createTable(stmt);
	runArray(dbc, stmt);
	dumpResults("runArray", stmt);
	finish(env, dbc, stmt, false);
	return 0;
}

void runBatch(SQLHDBC dbc, SQLHSTMT stmt)
{
	SQLRETURN sr;
	int c1 = 0;
	SQLCHAR buffer[60];
	SQLLEN l1 = sizeof(c1);
	SQLLEN l2 = ARRAY_SIZE(buffer);
	SQLLEN rowCount = 0;
	// Setting the SQL_ATTR_BATCH_PARAMS attribute to start the batch
	sr = SQLSetConnectAttr(dbc, SQL_ATTR_BATCH_PARAMS, (SQLPOINTER)SQL_BATCH_ENABLED, SQL_IS_INTEGER);
	printError(sr, SQL_HANDLE_DBC, dbc);
	// Bind the parameters. This can be done once for the entire batch
	sr = SQLBindParameter(stmt, 1, SQL_PARAM_INPUT, SQL_C_LONG, SQL_INTEGER, l1, 0, &c1, l1, &l1);
	sr = SQLBindParameter(stmt, 2, SQL_PARAM_INPUT, SQL_C_CHAR, SQL_LONGVARCHAR, l2, 0, buffer, l2, &l2);

	// Run a batch
	for (int i = 0; i < BATCH_SIZE; i++)
	{
		c1 = i;
		memset(buffer, 'a' + i % 26, l2);
		sr = SQLExecDirect(stmt, insertStmt, SQL_NTS);
		printError(sr, SQL_HANDLE_STMT, stmt);
	}

	// Setting the SQL_ATTR_BATCH_PARAMS attribute to end the batch
	sr = SQLSetConnectAttr(dbc, SQL_ATTR_BATCH_PARAMS, (SQLPOINTER)SQL_BATCH_LAST_NO_DATA, SQL_IS_INTEGER);
	printError(sr, SQL_HANDLE_DBC, dbc);
	// Call SQLExecDirect one more time to close the batch
	// - Due to SQL_BATCH_LAST_NO_DATA, this will not process the parameters
	sr = SQLExecDirect(stmt, insertStmt, SQL_NTS);
	printError(sr, SQL_HANDLE_STMT, stmt);
	// Report the number of rows inserted by the batch
	sr = SQLRowCount(stmt, &rowCount);
	printError(sr, SQL_HANDLE_STMT, stmt);
	printf("SQLRowCount: %i\n", (int)rowCount);
	// Cleanup the statement handle
	sr = SQLFreeStmt(stmt, SQL_UNBIND);
	sr = SQLFreeStmt(stmt, SQL_RESET_PARAMS);
	sr = SQLFreeStmt(stmt, SQL_CLOSE);
}

void runArray(SQLHDBC dbc, SQLHSTMT stmt)
{
	SQLRETURN sr;
	int c1[BATCH_SIZE];
	SQLCHAR buffer[BATCH_SIZE][60];
	SQLLEN l1 = sizeof(c1);
	SQLLEN l2 = ARRAY_SIZE(buffer[0]);
	SQLLEN l1Array[BATCH_SIZE];
	SQLLEN l2Array[BATCH_SIZE];
	SQLLEN rowCount = 0;
	// Bind the parameters
	// NOTE: In runBatch, we bind the second parameter as SQL_LONGVARCHAR. This is
	// possible, acceptable, and required. However, when using the standard interface
	// and binding an array of parameters, then the use of SQL_LONGVARCHAR is not
	// allowed due to memory consumption. To mimic this behavior we bind as SQL_VARCHAR
	sr = SQLSetStmtAttr(stmt, SQL_ATTR_PARAMSET_SIZE, (SQLPOINTER)BATCH_SIZE, SQL_IS_INTEGER);
	sr = SQLBindParameter(stmt, 1, SQL_PARAM_INPUT, SQL_C_LONG, SQL_INTEGER, l1, 0, c1, l1, l1Array);
	sr = SQLBindParameter(stmt, 2, SQL_PARAM_INPUT, SQL_C_CHAR, SQL_VARCHAR, l2, 0, buffer, l2, l2Array);

	// Run a batch
	for (int i = 0; i < BATCH_SIZE; i++)
	{
		c1[i] = i;
		memset(buffer[i], 'a' + i % 26, l2);
		l1Array[i] = l1;
		l2Array[i] = l2;
	}

	sr = SQLExecDirect(stmt, insertStmt, SQL_NTS);
	printError(sr, SQL_HANDLE_STMT, stmt);
	// Report the number of rows inserted by the batch
	sr = SQLRowCount(stmt, &rowCount);
	printError(sr, SQL_HANDLE_STMT, stmt);
	printf("SQLRowCount: %i\n", (int)rowCount);
	// Cleanup the statement handle
	sr = SQLFreeStmt(stmt, SQL_UNBIND);
	sr = SQLFreeStmt(stmt, SQL_RESET_PARAMS);
	sr = SQLFreeStmt(stmt, SQL_CLOSE);
}

void dumpResults(char* title, SQLHSTMT stmt)
{
	SQLRETURN sr;
	int c1 = 0;
	SQLCHAR buffer[100];
	SQLLEN l1 = sizeof(c1);
	SQLLEN l2 = ARRAY_SIZE(buffer);
	printf("%s:\n", title);
	sr = SQLExecDirect(stmt, selectStmt, SQL_NTS);
	printError(sr, SQL_HANDLE_STMT, stmt);
	sr = SQLBindCol(stmt, 1, SQL_C_LONG, &c1, l1, &l1);
	sr = SQLBindCol(stmt, 2, SQL_C_CHAR, buffer, l2, &l2);

	while (SQLFetch(stmt) != SQL_NO_DATA)
	{
		printf("%i, %s\n", c1, (char*)buffer);
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
	sr = SQLAllocHandle(SQL_HANDLE_ENV, SQL_NULL_HANDLE, env);

	if (sr != SQL_SUCCESS && sr != SQL_SUCCESS_WITH_INFO)
	{
		printf("Allocating Environment Handle failed; SQLRETURN code is :%i", (int)sr);
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
		memcpy(connString, tmpConnString.c_str(), tmpConnString.length()*sizeof(SQLTCHAR));
		connString[tmpConnString.length()] = 0;
#else
		//The connection string is hard coded because wmain is non-standared c++
		//A complete string converter, which is not in the scope of this sample, would be required for command line input
		//NOTE we are only able to build with UNICODE defined on platforms that allow the
		//redefinition of wchar_t from 32bit to 16bit to match SQLWCHAR
		cout << "Using connection string \"DSN=sampledsn\"" << endl;
		memcpy(connString, _ODBCSTRTYPE("DSN=sampledsn"), lengthOfDefault*sizeof(SQLTCHAR));
		connString[lengthOfDefault] = 0;
#endif
#else
		string tmpConnString = string("DSN=");
		tmpConnString += string(argv[1]);
		tmpConnString += string(";UID=");
		tmpConnString += string(argv[2]);
		tmpConnString += string(";PWD=");
		tmpConnString += string(argv[3]);
		cout << "Using connection string \"" << tmpConnString.c_str() << "\"" << endl;
		memcpy(connString, tmpConnString.c_str(), tmpConnString.length()*sizeof(SQLTCHAR));
		connString[tmpConnString.length()] = 0;
#endif
	}
	else
	{
		cout << "Using connection string \"DSN=sampledsn\"" << endl;
		memcpy(connString, _ODBCSTRTYPE("DSN=sampledsn"), lengthOfDefault*sizeof(SQLTCHAR));
		connString[lengthOfDefault] = 0;
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
			printf("SqlState: %s Error Message: %s\n", (char*)sqlstate, (char*)errormsg);
		}

		exit(1);
	}
}
