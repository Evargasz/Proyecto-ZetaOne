/*
Copyright (c) 2003-2010  Sybase, Inc.

Module Name:
	simple.cpp

Abstract:
 	Sample ODBC console application.
 	Executes a simple select statement and retrieves rows

*/


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
#if defined (WIN32) || defined(_WIN32)
#include <windows.h>
#else
#include <stdlib.h>
#include <stddef.h>
#endif
#include <string.h>
#include <sql.h>
#include <sqlext.h>
#include <iostream>
#ifdef LINUX
#ifndef SQLLEN
#define SQLLEN SQLINTEGER
#endif
#ifndef SQLULEN
#define SQLULEN SQLUINTEGER
#endif
#endif
void finish(SQLHENV env, SQLHDBC dbc, SQLHSTMT stmt, bool doExit);
void sqlok(SQLHSTMT stmt, SQLRETURN retcode, char* message, SQLSMALLINT handleType = SQL_HANDLE_STMT);
using namespace std;

#define AU_ID_LEN 12
#define STMT_LEN 100
#define AU_FNAME_LEN 21
#define ERR_MSG_LEN	255

#if defined(WIN32) && defined(UNICODE)
int wmain(int argc, wchar_t* argv[])
#else
int main(int argc, char* argv[])
#endif
{
	SQLLEN 		aufNameLen = 0;
	SQLCHAR		aufName[ AU_FNAME_LEN ];
	SQLHENV		env	= SQL_NULL_HANDLE;
	SQLHDBC		dbc	= SQL_NULL_HANDLE;
	SQLHSTMT 	stmt = SQL_NULL_HANDLE;
	SQLRETURN 	retcode;
	SQLTCHAR	connString[512];
	SQLTCHAR*	 selectstmt = _ODBCSTRTYPE("select au_fname from authors ");
	retcode = SQLAllocHandle(SQL_HANDLE_ENV, SQL_NULL_HANDLE, &env);
	int lengthOfDefault = strlen("DSN=sampledsn");

	if (retcode != SQL_SUCCESS && retcode != SQL_SUCCESS_WITH_INFO)
	{
		cout << "Allocating environment handle failed; SQLRETURN code is :" << retcode << endl;
		exit(1);
	}

	/* Set the ODBC version environment attribute */
	SQLSetEnvAttr(env, SQL_ATTR_ODBC_VERSION, (void*)SQL_OV_ODBC3, 0);

	retcode = SQLAllocHandle(SQL_HANDLE_DBC, env, &dbc);
	sqlok(env, retcode, (char *)"Allocating connection handle failed", SQL_HANDLE_ENV);

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
		//The connection string is hard-coded because wmain is non-standard C++
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
	retcode = SQLDriverConnect(dbc, SQL_NULL_HANDLE, connString, SQL_NTS, SQL_NULL_HANDLE, 0, SQL_NULL_HANDLE, SQL_DRIVER_NOPROMPT);
	sqlok(stmt, retcode, (char *)"Obtaining a connection failed");

	retcode = SQLAllocHandle(SQL_HANDLE_STMT, dbc, &stmt);
	sqlok(stmt, retcode, (char *)"Allocating statement handle failed");

	retcode = SQLExecDirect(stmt, selectstmt, SQL_NTS) ;
	sqlok(stmt, retcode, (char *)"SQLExecDirect failed");

	retcode = SQLBindCol(stmt, 1, SQL_C_CHAR, aufName, sizeof(aufName), &aufNameLen);
	sqlok(stmt, retcode, (char *)"SQLBindCol failed");

	while (retcode == SQL_SUCCESS || retcode == SQL_SUCCESS_WITH_INFO)
	{
		retcode = SQLFetch(stmt);
		sqlok(stmt, retcode, (char *)"Fetching result set failed");

		cout << "Author FirstName : " << aufName << endl;
		cout << " : Length of Author FirstName :" << aufNameLen <<	endl ;
	}//end while

	cout << " End of Sample " << endl;
	finish(env, dbc, stmt, false);
	return 0;
}

void finish(SQLHENV env, SQLHDBC dbc, SQLHSTMT stmt, bool doExit)
{
	if (stmt != SQL_NULL_HANDLE)
	{
		SQLFreeStmt(stmt, SQL_CLOSE); //close the result set
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

void sqlok(SQLHSTMT stmt, SQLRETURN retcode, char* message, SQLSMALLINT handleType)
{
	SQLTCHAR errormsg[ERR_MSG_LEN], sqlstate[SQL_SQLSTATE_SIZE+1];
	SQLINTEGER nativeerror = 0;
	SQLSMALLINT errormsglen = 0;
	if (retcode != SQL_SUCCESS && retcode != SQL_SUCCESS_WITH_INFO && retcode != SQL_NO_DATA)
	{
		cout << message << endl;
		cout << "SQLRETURN code is " << retcode << endl;
		if (retcode == SQL_ERROR)
		{
			retcode = SQLGetDiagRec(handleType, stmt, 1, sqlstate, &nativeerror, errormsg, ERR_MSG_LEN, &errormsglen);

			if (retcode == SQL_SUCCESS || retcode == SQL_SUCCESS_WITH_INFO)
			{
				cout << " SqlState : ";
				TCOUT << sqlstate;
				cout << " Error Message :";
				TCOUT << errormsg;
				cout << endl ;
			}
		}
		exit(1);
	}
}
